// JavaScript untuk kamera dan upload
document.addEventListener('DOMContentLoaded', function () {
    const cameraContainer = document.getElementById('camera-container');
    const imagePreview = document.getElementById('image-preview');
    const captureBtn = document.getElementById('capture-btn');
    const retakeBtn = document.getElementById('retake-btn');
    const uploadBtn = document.getElementById('upload-btn');
    const imageUpload = document.getElementById('image-upload');
    const capturedImage = document.getElementById('captured-image');

    let stream;
    let capturedBlob;

    // Akses kamera
    async function startCamera() {
        try {
            const video = document.getElementById('camera-preview');
            stream = await navigator.mediaDevices.getUserMedia({ video: true });
            video.srcObject = stream;
        } catch (err) {
            console.error("Error mengakses kamera:", err);
            cameraContainer.innerHTML = `
                <div class="alert alert-warning">
                    Kamera tidak tersedia. Silakan unggah gambar dari file.
                </div>
                <button id="upload-fallback" class="btn btn-primary w-100">Pilih File</button>
            `;
            document.getElementById('upload-fallback').addEventListener('click', () => {
                imageUpload.click();
            });
        }
    }

    // Tangkap gambar dari kamera
    captureBtn.addEventListener('click', function () {
        const video = document.getElementById('camera-preview');
        const canvas = document.createElement('canvas');
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        const ctx = canvas.getContext('2d');
        ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

        canvas.toBlob((blob) => {
            capturedBlob = blob;
            capturedImage.src = URL.createObjectURL(blob);
            cameraContainer.classList.add('d-none');
            imagePreview.classList.remove('d-none');
        }, 'image/jpeg', 0.9);
    });

    // Ulangi pengambilan gambar
    retakeBtn.addEventListener('click', function () {
        imagePreview.classList.add('d-none');
        cameraContainer.classList.remove('d-none');
        startCamera();
    });

    // Upload file
    uploadBtn.addEventListener('click', function () {
        imageUpload.click();
    });

    imageUpload.addEventListener('change', function (e) {
        if (e.target.files[0]) {
            const file = e.target.files[0];
            const reader = new FileReader();

            reader.onload = function (event) {
                capturedImage.src = event.target.result;
                cameraContainer.classList.add('d-none');
                imagePreview.classList.remove('d-none');
            };

            reader.readAsDataURL(file);
        }
    });

    // Mulai kamera saat halaman dimuat
    startCamera();
});