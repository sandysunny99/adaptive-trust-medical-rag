import { useEffect, useId, useLayoutEffect, useRef, useState, type ChangeEvent, type DragEvent } from 'react';
import { AlertTriangle, Upload } from 'lucide-react';
import { ALLOWED_PRESCRIPTION_IMAGE_TYPES, validatePrescriptionImage } from '../services/prescriptionImage';
import { cn } from '../utils/cn';

interface PrescriptionDropzoneProps {
  file: File | null;
  onFileChange: (file: File | null) => void;
  disabled?: boolean;
}

function formatBytes(bytes: number) {
  if (bytes < 1024 * 1024) return `${Math.max(1, Math.round(bytes / 1024))} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

const isFileDrag = (e: { dataTransfer: DataTransfer | null }) =>
  Array.from(e.dataTransfer?.types ?? []).includes('Files');

const SECONDARY_BUTTON =
  'rounded-lg border border-input px-3 py-1.5 text-sm font-medium text-foreground hover:border-primary hover:text-primary ' +
  'focus:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50';

/**
 * Prescription image picker. Drag and drop and the file picker are handled
 * explicitly instead of relying on an invisible native file input, so the
 * zone works the same in every browser and invalid files get a visible reason.
 */
export function PrescriptionDropzone({ file, onFileChange, disabled = false }: PrescriptionDropzoneProps) {
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const zoneRef = useRef<HTMLDivElement>(null);
  const previewRef = useRef<HTMLImageElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const dragDepthRef = useRef(0);
  const hintId = useId();

  // The preview's object URL lives exactly as long as the file is shown (and is
  // recreated if the zone remounts, e.g. after switching input mode and back).
  useLayoutEffect(() => {
    if (!file || !previewRef.current) return;
    const url = URL.createObjectURL(file);
    previewRef.current.src = url;
    return () => URL.revokeObjectURL(url);
  }, [file]);

  // A file dropped just outside the zone would otherwise replace the app with the image.
  useEffect(() => {
    const guard = (e: globalThis.DragEvent) => {
      if (!isFileDrag(e) || zoneRef.current?.contains(e.target as Node)) return;
      e.preventDefault();
      if (e.dataTransfer) e.dataTransfer.dropEffect = 'none';
    };
    window.addEventListener('dragover', guard);
    window.addEventListener('drop', guard);
    return () => {
      window.removeEventListener('dragover', guard);
      window.removeEventListener('drop', guard);
    };
  }, []);

  // An invalid replacement keeps the current image and explains why.
  const selectFiles = (files: FileList | null) => {
    if (!files || files.length === 0) return;
    const check = validatePrescriptionImage(files);
    if (check.error !== null) {
      setUploadError(check.error);
      return;
    }
    setUploadError(null);
    onFileChange(check.file);
  };

  const openFilePicker = () => {
    if (!disabled) inputRef.current?.click();
  };

  const handleInputChange = (e: ChangeEvent<HTMLInputElement>) => {
    selectFiles(e.target.files);
    // Allow choosing the same file again after removing it.
    e.target.value = '';
  };

  const removeImage = () => {
    setUploadError(null);
    onFileChange(null);
  };

  const handleDragEnter = (e: DragEvent<HTMLDivElement>) => {
    if (!isFileDrag(e)) return;
    e.preventDefault();
    dragDepthRef.current += 1;
    setIsDragging(true);
  };

  const handleDragOver = (e: DragEvent<HTMLDivElement>) => {
    if (!isFileDrag(e)) return;
    e.preventDefault();
    e.dataTransfer.dropEffect = disabled ? 'none' : 'copy';
  };

  // Entering a child element fires dragleave on the parent; count depth to avoid flicker.
  const handleDragLeave = (e: DragEvent<HTMLDivElement>) => {
    if (!isFileDrag(e)) return;
    e.preventDefault();
    dragDepthRef.current = Math.max(0, dragDepthRef.current - 1);
    if (dragDepthRef.current === 0) setIsDragging(false);
  };

  const handleDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    dragDepthRef.current = 0;
    setIsDragging(false);
    if (!disabled) selectFiles(e.dataTransfer.files);
  };

  return (
    <div>
      <div
        ref={zoneRef}
        role="group"
        aria-label="Prescription image upload"
        aria-describedby={hintId}
        data-testid="prescription-dropzone"
        data-dragging={isDragging}
        onDragEnter={handleDragEnter}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={e => {
          // Mouse users can click anywhere on the empty zone; the Browse button is the keyboard path.
          if (!file && !(e.target as HTMLElement).closest('button')) openFilePicker();
        }}
        className={cn(
          'rounded-lg border-2 border-dashed p-8 text-center transition-colors',
          isDragging ? 'border-primary bg-primary-soft'
            : uploadError ? 'border-destructive'
            : 'border-input hover:border-primary',
          !file && !disabled && 'cursor-pointer',
        )}
      >
        {file ? (
          <div className="flex flex-col items-center gap-3">
            <img
              ref={previewRef}
              alt={`Preview of ${file.name}`}
              className="max-h-48 max-w-full rounded border border-border object-contain"
            />
            <p className="text-sm text-foreground">
              <span className="font-medium">{file.name}</span>{' '}
              <span className="text-muted-foreground">({formatBytes(file.size)})</span>
            </p>
            <div className="flex gap-2">
              <button type="button" onClick={openFilePicker} disabled={disabled} className={SECONDARY_BUTTON}>
                Replace image
              </button>
              <button
                type="button"
                onClick={removeImage}
                disabled={disabled}
                className={cn(SECONDARY_BUTTON, 'hover:border-destructive hover:text-destructive')}
              >
                Remove image
              </button>
            </div>
          </div>
        ) : (
          <>
            <Upload className="mx-auto text-muted-foreground mb-3" size={32} aria-hidden="true" />
            <p className="text-sm text-foreground">
              {isDragging ? 'Drop the image to upload it' : 'Drag & drop a prescription image here, or'}
            </p>
            <button
              type="button"
              onClick={openFilePicker}
              disabled={disabled}
              aria-describedby={hintId}
              className={cn(SECONDARY_BUTTON, 'mt-3 px-4 py-2 text-primary')}
            >
              Browse files
            </button>
          </>
        )}
        <p id={hintId} className="mt-2 text-xs text-muted-foreground">
          One JPEG, PNG or WEBP image • Max 5 MB
        </p>
      </div>
      <input
        ref={inputRef}
        type="file"
        className="hidden"
        tabIndex={-1}
        aria-label="Prescription image file"
        accept={ALLOWED_PRESCRIPTION_IMAGE_TYPES.join(',')}
        onChange={handleInputChange}
      />
      {uploadError && (
        <p role="alert" className="mt-2 flex items-start gap-1.5 text-sm text-destructive">
          <AlertTriangle size={14} className="mt-0.5 shrink-0" aria-hidden="true" />
          {uploadError}
        </p>
      )}
    </div>
  );
}
