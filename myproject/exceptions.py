from rest_framework.exceptions import APIException
from rest_framework import status

class ValidationError(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'Ошибка валидации данных'
    default_code = 'validation_error'

class AuthenticationError(APIException):
    status_code = status.HTTP_401_UNAUTHORIZED
    default_detail = 'Ошибка аутентификации'
    default_code = 'authentication_error'

class PermissionError(APIException):
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = 'Недостаточно прав для выполнения операции'
    default_code = 'permission_error'

class NotFoundError(APIException):
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = 'Запрашиваемый ресурс не найден'
    default_code = 'not_found_error'

class ConflictError(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = 'Конфликт данных'
    default_code = 'conflict'

class ServerError(APIException):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = 'Внутренняя ошибка сервера'
    default_code = 'server_error'

class JobNotFoundError(NotFoundError):
    default_detail = 'Вакансия не найдена'
    default_code = 'job_not_found'

class ApplicationNotFoundError(NotFoundError):
    default_detail = 'Заявка не найдена'
    default_code = 'application_not_found'

class UserNotFoundError(NotFoundError):
    default_detail = 'Пользователь не найден'
    default_code = 'user_not_found'

class DepartmentNotFoundError(NotFoundError):
    default_detail = 'Отдел не найден'
    default_code = 'department_not_found'

class InvalidApplicationStatusError(ValidationError):
    default_detail = 'Некорректный статус заявки'
    default_code = 'invalid_application_status'

class ApplicationAlreadyExistsError(ConflictError):
    default_detail = 'Заявка на эту вакансию уже существует'
    default_code = 'application_already_exists'

class JobDeadlineExpiredError(ValidationError):
    default_detail = 'Срок подачи заявки истек'
    default_code = 'job_deadline_expired'

class InvalidFileTypeError(ValidationError):
    default_detail = 'Неподдерживаемый тип файла'
    default_code = 'invalid_file_type'

class FileTooLargeError(ValidationError):
    default_detail = 'Файл слишком большой'
    default_code = 'file_too_large' 