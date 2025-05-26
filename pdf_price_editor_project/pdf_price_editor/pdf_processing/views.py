from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from .models import PdfDocument
import os

@csrf_exempt
@login_required
def upload_pdf(request):
    if request.method == 'POST':
        if not request.FILES.get('file'):
            return JsonResponse({'error': 'No file provided.'}, status=400)

        uploaded_file = request.FILES['file']
        
        # Basic validation: check for .pdf extension and non-empty file
        file_name_lower = uploaded_file.name.lower()
        if not file_name_lower.endswith('.pdf'):
            return JsonResponse({'error': 'Invalid file type, only PDF is allowed.'}, status=400)
        
        if not uploaded_file.size > 0:
            return JsonResponse({'error': 'The uploaded file is empty.'}, status=400)

        # More robust validation (e.g., actual PDF content type, size limits) can be added here.

        try:
            pdf_doc = PdfDocument(
                user=request.user,
                uploaded_file=uploaded_file
                # file_name is set in the model's save() method
            )
            pdf_doc.save() # This will also set the file_name

            return JsonResponse({
                'status': 'success',
                'message': 'File uploaded successfully.',
                'document_id': pdf_doc.id,
                'file_name': pdf_doc.file_name 
            }, status=201)
        except Exception as e:
            # Log the exception e
            return JsonResponse({'error': f'An error occurred during file upload: {str(e)}'}, status=500)
    else:
        return JsonResponse({'error': 'Only POST requests are allowed'}, status=405)

@login_required # No @csrf_exempt needed for GET usually
def download_modified_pdf_view(request, document_id):
    if request.method == 'GET':
        try:
            pdf_doc = PdfDocument.objects.get(id=document_id, user=request.user)
        except PdfDocument.DoesNotExist:
            return JsonResponse({'error': 'Document not found or access denied.'}, status=404)

        if pdf_doc.modified_file and pdf_doc.modified_file.path:
            try:
                # Ensure the file physically exists
                if not os.path.exists(pdf_doc.modified_file.path):
                    # Log this critical error: file missing from filesystem
                    print(f"Error: Modified file for document ID {document_id} not found at path {pdf_doc.modified_file.path}")
                    return JsonResponse({'error': 'Modified file not found on server.'}, status=404)

                # Determine a user-friendly filename for download
                original_filename_base, original_filename_ext = os.path.splitext(pdf_doc.file_name or "document")
                download_filename = f"{original_filename_base}_modified{original_filename_ext}"
                
                # FileResponse handles setting Content-Disposition and Content-Type
                response = FileResponse(open(pdf_doc.modified_file.path, 'rb'), 
                                        as_attachment=True, 
                                        filename=download_filename)
                return response
            except Exception as e:
                # Log the exception e
                print(f"Error serving file for document ID {document_id}: {e}")
                return JsonResponse({'error': 'Error serving the modified file.'}, status=500)
        else:
            return JsonResponse({'error': 'No modified PDF available for download for this document.'}, status=404)
    else:
        return JsonResponse({'error': 'Only GET requests are allowed'}, status=405)

@csrf_exempt # Required for methods other than GET/POST if CSRF is generally enabled
@login_required
def delete_document_view(request, document_id):
    if request.method == 'DELETE':
        try:
            pdf_doc = PdfDocument.objects.get(id=document_id, user=request.user)
        except PdfDocument.DoesNotExist:
            return JsonResponse({'error': 'Document not found or access denied.'}, status=404)

        try:
            # Delete associated files first
            if pdf_doc.uploaded_file:
                # Check if file exists before trying to delete
                if os.path.exists(pdf_doc.uploaded_file.path):
                    pdf_doc.uploaded_file.delete(save=False) # save=False as we'll delete the model instance next
                else:
                    print(f"Warning: Original file not found at {pdf_doc.uploaded_file.path} for doc ID {pdf_doc.id} during delete.")
            
            if pdf_doc.modified_file:
                if os.path.exists(pdf_doc.modified_file.path):
                    pdf_doc.modified_file.delete(save=False)
                else:
                    print(f"Warning: Modified file not found at {pdf_doc.modified_file.path} for doc ID {pdf_doc.id} during delete.")

            # Delete the PdfDocument record from the database
            pdf_doc.delete()
            
            return JsonResponse({'status': 'success', 'message': 'Document deleted successfully.'}, status=200) # Or 204 No Content

        except Exception as e:
            # Log the exception e
            print(f"Error deleting document or its files for doc ID {pdf_doc.id}: {e}")
            # Potentially return a 500 error if deletion of files or model fails partially
            return JsonResponse({'error': f'An error occurred while deleting the document: {str(e)}'}, status=500)
            
    else:
        return JsonResponse({'error': 'Only DELETE requests are allowed'}, status=405)

@login_required
def list_user_documents_view(request):
    if request.method == 'GET':
        documents = PdfDocument.objects.filter(user=request.user).order_by('-upload_date')
        
        data = []
        for doc in documents:
            original_file_url = request.build_absolute_uri(doc.uploaded_file.url) if doc.uploaded_file else None
            modified_file_url = request.build_absolute_uri(doc.modified_file.url) if doc.modified_file else None
            
            data.append({
                'document_id': doc.id,
                'file_name': doc.file_name,
                'upload_date': doc.upload_date.strftime('%Y-%m-%d %H:%M:%S'), # Format datetime
                'status': doc.status,
                'original_file_url': original_file_url,
                'modified_file_url': modified_file_url,
            })
            
        return JsonResponse({'documents': data}, status=200)
    else:
        return JsonResponse({'error': 'Only GET requests are allowed'}, status=405)

@csrf_exempt
@login_required
def replace_text_region_view(request, document_id):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            page_number = data.get('page_number')
            x1 = data.get('x1')
            y1 = data.get('y1')
            x2 = data.get('x2')
            y2 = data.get('y2')
            percentage_increase = data.get('percentage_increase')
            original_price_text = data.get('original_price_text')
            style_info = data.get('style_info')

            if not all(isinstance(coord, (int, float)) for coord in [x1, y1, x2, y2]) or \
               not isinstance(page_number, int) or page_number < 0 or \
               not isinstance(percentage_increase, (int, float)) or \
               not isinstance(original_price_text, str) or not original_price_text or \
               not isinstance(style_info, dict):
                return JsonResponse({'error': 'Invalid or missing required parameters in request body.'}, status=400)

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON payload.'}, status=400)
        except Exception as e:
            return JsonResponse({'error': f'Error processing request: {str(e)}'}, status=400)

        try:
            pdf_doc = PdfDocument.objects.get(id=document_id, user=request.user)
        except PdfDocument.DoesNotExist:
            return JsonResponse({'error': 'Document not found or access denied.'}, status=404)

        if not pdf_doc.uploaded_file or not pdf_doc.uploaded_file.path:
            return JsonResponse({'error': 'Original file path not found for document.'}, status=500)
        
        original_pdf_path = pdf_doc.uploaded_file.path
        if not os.path.exists(original_pdf_path):
            print(f"Error: Original file for document ID {document_id} not found at path {original_pdf_path}")
            return JsonResponse({'error': 'Original file not found on server.'}, status=500)

        from .utils import replace_text_in_pdf_region, parse_price_string, format_new_price

        # Calculate new price
        original_price_value = parse_price_string(original_price_text)
        if original_price_value is None: # parse_price_string now returns 0.0 on error, so this check may change
             return JsonResponse({'error': f'Could not parse original price text: {original_price_text}'}, status=400)
        
        new_price_value = original_price_value * (1 + (float(percentage_increase) / 100.0))
        new_price_text = format_new_price(original_price_text, new_price_value)

        # Prepare style arguments from style_info
        font_name = style_info.get('font', 'Helvetica')
        font_size = style_info.get('size', 10.0)
        text_color_hex = style_info.get('color', '#000000')
        is_bold = style_info.get('bold', False)
        is_italic = style_info.get('italic', False)

        # Define output path for the modified PDF
        # Example: MEDIA_ROOT/user_<id>/pdfs/modified/original_filename_modified_timestamp.pdf
        base_filename = os.path.basename(original_pdf_path)
        name, ext = os.path.splitext(base_filename)
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        modified_filename = f"{name}_mod_{timestamp}{ext}"
        
        # Construct path within MEDIA_ROOT using the user_directory_path logic if possible, or manually
        # Assuming user_directory_path places it in user_<id>/pdfs/originals/
        # So, modified path should be user_<id>/pdfs/modified/
        user_specific_modified_dir = os.path.join(settings.MEDIA_ROOT, f'user_{pdf_doc.user.id}', 'pdfs', 'modified')
        if not os.path.exists(user_specific_modified_dir):
            os.makedirs(user_specific_modified_dir, exist_ok=True)
        output_pdf_path = os.path.join(user_specific_modified_dir, modified_filename)
        
        success = replace_text_in_pdf_region(
            original_pdf_path, page_number, x1, y1, x2, y2, new_price_text,
            font_name, font_size, text_color_hex, is_bold, is_italic,
            output_pdf_path
        )

        if success:
            # Save the path to the modified file in PdfDocument
            # The path stored should be relative to MEDIA_ROOT for FileField
            relative_output_path = os.path.join(f'user_{pdf_doc.user.id}', 'pdfs', 'modified', modified_filename)
            pdf_doc.modified_file.name = relative_output_path # Assign to .name for FileField
            pdf_doc.status = 'completed' # Or a more specific status like 'modified'
            pdf_doc.save()
            
            return JsonResponse({
                'status': 'success',
                'message': 'Text replaced successfully.',
                'modified_document_id': pdf_doc.id,
                'new_price_text': new_price_text,
                'modified_file_url': request.build_absolute_uri(pdf_doc.modified_file.url) if pdf_doc.modified_file else None
            }, status=200)
        else:
            pdf_doc.status = 'failed'
            pdf_doc.save()
            return JsonResponse({'error': 'Failed to replace text in PDF.'}, status=500)
            
    else:
        return JsonResponse({'error': 'Only POST requests are allowed'}, status=405)

@csrf_exempt
@login_required
def analyze_text_style_view(request, document_id):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            page_number = data.get('page_number')
            x1 = data.get('x1')
            y1 = data.get('y1')
            x2 = data.get('x2')
            y2 = data.get('y2')

            if not all(isinstance(coord, (int, float)) for coord in [x1, y1, x2, y2]) or \
               not isinstance(page_number, int) or page_number < 0:
                return JsonResponse({'error': 'Invalid or missing coordinates or page number.'}, status=400)

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON payload.'}, status=400)
        except Exception as e:
            return JsonResponse({'error': f'Error processing request: {str(e)}'}, status=400)

        try:
            pdf_doc = PdfDocument.objects.get(id=document_id, user=request.user)
        except PdfDocument.DoesNotExist:
            return JsonResponse({'error': 'Document not found or access denied.'}, status=404)

        if not pdf_doc.uploaded_file or not pdf_doc.uploaded_file.path:
            return JsonResponse({'error': 'File path not found for document.'}, status=500)
        
        pdf_path = pdf_doc.uploaded_file.path
        if not os.path.exists(pdf_path):
            print(f"Error: File for document ID {document_id} not found at path {pdf_path}")
            return JsonResponse({'error': 'File not found on server for style analysis.'}, status=500)

        from .utils import get_text_style_in_region # Local import

        style_info = get_text_style_in_region(pdf_path, page_number, x1, y1, x2, y2)

        if style_info:
            # If the function returns a message (e.g. "No text found..."), it's not an error but an outcome.
            if "message" in style_info and style_info.get("text") == "":
                 return JsonResponse({
                    'status': 'success', # Still a success, but with a message
                    'document_id': pdf_doc.id,
                    'region_coordinates': [x1, y1, x2, y2],
                    'style_info': style_info
                }, status=200) # OK, but maybe no text
            
            return JsonResponse({
                'status': 'success',
                'document_id': pdf_doc.id,
                'region_coordinates': [x1, y1, x2, y2],
                'style_info': style_info
            }, status=200)
        else:
            # This 'else' implies a more critical failure in the utility function (returned None)
            return JsonResponse({'error': 'Failed to analyze text style for the specified region.'}, status=500)
    else:
        return JsonResponse({'error': 'Only POST requests are allowed'}, status=405)

@csrf_exempt
@login_required
def ocr_text_from_region_view(request, document_id):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            page_number = data.get('page_number')
            x1 = data.get('x1')
            y1 = data.get('y1')
            x2 = data.get('x2')
            y2 = data.get('y2')
            language = data.get('language', 'eng') # Default to English if not provided

            if not all(isinstance(coord, (int, float)) for coord in [x1, y1, x2, y2]) or \
               not isinstance(page_number, int) or page_number < 0:
                return JsonResponse({'error': 'Invalid or missing coordinates or page number.'}, status=400)

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON payload.'}, status=400)
        except Exception as e: # Catch any other error during request parsing
            return JsonResponse({'error': f'Error processing request: {str(e)}'}, status=400)

        try:
            pdf_doc = PdfDocument.objects.get(id=document_id, user=request.user)
        except PdfDocument.DoesNotExist:
            return JsonResponse({'error': 'Document not found or access denied.'}, status=404)

        if not pdf_doc.uploaded_file or not pdf_doc.uploaded_file.path:
            return JsonResponse({'error': 'File path not found for document.'}, status=500)
        
        pdf_path = pdf_doc.uploaded_file.path
        if not os.path.exists(pdf_path):
            # Log this critical error: file missing from filesystem
            print(f"Error: File for document ID {document_id} not found at path {pdf_path}")
            return JsonResponse({'error': 'File not found on server for OCR.'}, status=500)

        from .utils import extract_text_from_region_ocr # Local import

        ocr_text = extract_text_from_region_ocr(pdf_path, page_number, x1, y1, x2, y2, language=language)

        if ocr_text is not None:
            return JsonResponse({
                'status': 'success',
                'document_id': pdf_doc.id,
                'region_coordinates': [x1, y1, x2, y2],
                'ocr_text': ocr_text,
                'language_used': language
            }, status=200)
        else:
            # Check if Tesseract is installed if specific error occurs
            if "Tesseract is not installed" in str(ocr_text_or_error_msg_if_any_from_util_func): # This part is pseudo-code
                 return JsonResponse({'error': 'OCR processing failed: Tesseract might not be installed or configured correctly on the server.'}, status=500)
            return JsonResponse({'error': 'OCR processing failed for the specified region.'}, status=500)
    else:
        return JsonResponse({'error': 'Only POST requests are allowed'}, status=405)

@csrf_exempt
@login_required
def identify_prices_view(request, document_id):
    if request.method == 'POST':
        try:
            pdf_doc = PdfDocument.objects.get(id=document_id, user=request.user)
        except PdfDocument.DoesNotExist:
            return JsonResponse({'error': 'Document not found or access denied.'}, status=404)

        if not pdf_doc.extracted_text:
            # Optionally, could trigger text extraction here if not done
            # For now, require text to be extracted first.
            pdf_doc.status = 'failed' # Or a more specific status like 'text_extraction_pending'
            pdf_doc.save()
            return JsonResponse({'error': 'Text has not been extracted from this document yet.'}, status=400)
        
        from .utils import identify_prices_in_text # Local import

        identified_prices = identify_prices_in_text(pdf_doc.extracted_text)

        # You might want a new status like 'prices_identified'
        # For now, let's assume 'completed' covers this stage if successful.
        # If price identification is a distinct step that can fail, add appropriate status.
        if identified_prices is not None: # identify_prices_in_text returns [] for no prices, not None for error
            # pdf_doc.status = 'prices_identified' # Example of a new status
            # pdf_doc.save()
            return JsonResponse({
                'status': 'success',
                'document_id': pdf_doc.id,
                'file_name': pdf_doc.file_name,
                'identified_prices': identified_prices
            }, status=200)
        else:
            # This 'else' might not be reachable if identify_prices_in_text always returns a list.
            # It depends on its error handling. Assuming it could return None for a major internal error.
            pdf_doc.status = 'failed' # Or 'price_identification_failed'
            pdf_doc.save()
            return JsonResponse({'error': 'Failed to identify prices in the document.'}, status=500)
            
    else:
        return JsonResponse({'error': 'Only POST requests are allowed'}, status=405)

@csrf_exempt
@login_required
def extract_pdf_text_view(request, document_id):
    if request.method == 'POST':
        try:
            pdf_doc = PdfDocument.objects.get(id=document_id, user=request.user)
        except PdfDocument.DoesNotExist:
            return JsonResponse({'error': 'Document not found or access denied.'}, status=404)

        if not pdf_doc.uploaded_file or not pdf_doc.uploaded_file.path:
            return JsonResponse({'error': 'File path not found for document.'}, status=500)
            
        pdf_path = pdf_doc.uploaded_file.path
        
        # Ensure the file actually exists at the path stored
        if not os.path.exists(pdf_path):
            pdf_doc.status = 'failed'
            pdf_doc.save()
            # Log this critical error: file missing from filesystem
            print(f"Error: File for document ID {document_id} not found at path {pdf_path}")
            return JsonResponse({'error': 'File not found on server.'}, status=500)

        pdf_doc.status = 'processing'
        pdf_doc.save()

        from .utils import extract_text_from_pdf # Local import to avoid circular dependency if utils grows
        extracted_text = extract_text_from_pdf(pdf_path)

        if extracted_text is not None:
            pdf_doc.status = 'completed' # Assuming 'completed' means text extracted successfully
            pdf_doc.extracted_text = extracted_text # Save extracted text
            pdf_doc.save()
            return JsonResponse({
                'status': 'success',
                'document_id': pdf_doc.id,
                'file_name': pdf_doc.file_name,
                'extracted_text': extracted_text
            }, status=200)
        else:
            pdf_doc.status = 'failed'
            pdf_doc.save()
            return JsonResponse({'error': 'Failed to extract text from PDF.'}, status=500)
    else:
        return JsonResponse({'error': 'Only POST requests are allowed'}, status=405)
