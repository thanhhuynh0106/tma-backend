const multer = require('multer');
const { v2: cloudinary } = require('cloudinary');
const { CloudinaryStorage } = require('multer-storage-cloudinary');

// Cấu hình Cloudinary từ .env
cloudinary.config({
  cloud_name: process.env.CLOUDINARY_CLOUD_NAME,
  api_key: process.env.CLOUDINARY_API_KEY,
  api_secret: process.env.CLOUDINARY_API_SECRET,
});

// === STORAGE: UPLOAD TRỰC TIẾP LÊN CLOUDINARY ===
const storage = new CloudinaryStorage({
  cloudinary,
  params: {
    folder: 'tma-tasks', // Thư mục trên Cloudinary
    allowed_formats: ['jpg', 'jpeg', 'png', 'gif', 'webp', 'pdf', 'doc', 'docx', 'xls', 'xlsx', 'txt'],
    resource_type: 'auto',
    public_id: (req, file) => {
      const ext = file.originalname.split('.').pop();
      const name = file.originalname.replace(`.${ext}`, '');
      return `${name}-${Date.now()}-${req.user._id}`;
    },
  },
});

// === FILE FILTER: GIỮ NGUYÊN NHƯ CŨ ===
const fileFilter = (req, file, cb) => {
  const allowedMimes = [
    'application/pdf',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/vnd.ms-excel',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'image/jpeg',
    'image/png',
    'image/gif',
    'image/webp',
    'text/plain'
  ];

  const allowedExtensions = ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.jpg', '.jpeg', '.png', '.gif', '.webp', '.txt'];

  const ext = '.' + file.originalname.split('.').pop().toLowerCase();
  const mime = file.mimetype;

  if (allowedExtensions.includes(ext) && allowedMimes.includes(mime)) {
    cb(null, true);
  } else {
    cb(new Error(`File type not allowed. Allowed: ${allowedExtensions.join(', ')}`), false);
  }
};

// === MULTER INSTANCE ===
const upload = multer({
  storage: storage,        // UPLOAD LÊN CLOUDINARY
  fileFilter: fileFilter,
  limits: {
    fileSize: 5 * 1024 * 1024 // 5MB
  }
});

// === MIDDLEWARE: GIỮ NGUYÊN TÊN FIELD ===
const uploadSingle = upload.single('attachment');     // Dùng trong addAttachment
const uploadMultiple = upload.array('attachments', 5); // Dùng trong addAttachmentBulk

// === ERROR HANDLER: GIỮ NGUYÊN ===
const uploadErrorHandler = (err, req, res, next) => {
  if (err instanceof multer.MulterError) {
    if (err.code === 'LIMIT_FILE_SIZE') {
      return res.status(400).json({
        success: false,
        error: 'File size exceeds 5MB limit'
      });
    }
    if (err.code === 'LIMIT_FILE_COUNT') {
      return res.status(400).json({
        success: false,
        error: 'Maximum 5 files allowed'
      });
    }
  }

  if (err) {
    return res.status(400).json({
      success: false,
      error: err.message
    });
  }

  next();
};

// === HELPER: LẤY URL TỪ CLOUDINARY ===
const getFileUrl = (file) => {
  return file.path; // Cloudinary trả về .path = URL công khai
};

// === HELPER: XÓA FILE TRÊN CLOUDINARY ===
const deleteFile = async (publicId) => {
  try {
    if (!publicId) return false;
    const result = await cloudinary.uploader.destroy(publicId);
    return result.result === 'ok';
  } catch (error) {
    console.error('Cloudinary delete error:', error);
    return false;
  }
};

// === VALIDATE FILE TRÊN CLOUDINARY (TÙY CHỌN) ===
const validateFileExists = async (publicId) => {
  try {
    if (!publicId) return false;
    const result = await cloudinary.api.resource(publicId);
    return !!result;
  } catch (error) {
    return false;
  }
};

module.exports = {
  uploadSingle,
  uploadMultiple,
  uploadErrorHandler,
  getFileUrl,
  deleteFile,
  validateFileExists,
  cloudinary // export để dùng xóa ở controller
};