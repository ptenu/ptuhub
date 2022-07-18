import tempfile

import boto3
import falcon
from falcon.errors import HTTPInternalServerError
import settings

s3 = boto3.client(
    "s3",
    aws_access_key_id=settings.config["aws"].get("access_key"),
    aws_secret_access_key=settings.config["aws"].get("secret"),
)


class FileService:
    CDN_BUCKET = "ptu-static"
    CDN_ROOT_URL = "https://static.peterboroughtenants.app"
    PRIVATE_BUCKET = "ptu-secure"

    def store_file_public(self, file_obj, file_id):
        """
        Stores a file to the public CDN bucket.
        Files stored will be accessable to the public and could be
        viewed even if the URL was not shared.
        """

        env_name = settings.config["default"].get("env", "default")
        path = f"hub/{env_name}/{file_id}"
        try:
            s3.upload_fileobj(file_obj, self.CDN_BUCKET, path)
        except:
            raise falcon.HTTPInternalServerError(
                description="Error while trying to store file."
            )

        return self.CDN_BUCKET, path

    def get_public_url(self, file):
        """
        Get the public URL of a file (must be stored in the public bucket)
        """

        if file.bucket != self.CDN_BUCKET:
            raise falcon.HTTPNotFound()

        return self.CDN_ROOT_URL + "/" + file.key

    def get_file_size(self, file):
        """
        Returns the size in bites of a file
        """

        obj_info = s3.head_object(Bucket=file.bucket, Key=file.key)
        return obj_info["ContentLength"]

    def store_file_secure(self, file_obj, file_id):
        """
        Stores a file in a secure bucket which can only be accessed by authorised users
        and is encrypted at rest.
        """

        env_name = settings.config["default"].get("env", "default")
        path = f"{env_name}/{file_id}"
        try:
            s3.upload_fileobj(file_obj, self.PRIVATE_BUCKET, path)
        except:
            raise falcon.HTTPInternalServerError(
                description="Error while trying to store file."
            )

        return self.PRIVATE_BUCKET, path

    def get_file_object(self, bucket, key):
        """
        Download a file from S3
        """

        temp = tempfile.TemporaryFile()
        try:
            s3.download_fileobj(bucket, key, temp)
        except:
            raise falcon.HTTPInternalServerError(
                description="There was an error attempting to retrieve the file."
            )
        return temp

    def erase_file(self, bucket, key):
        try:
            response = s3.delete_object(Bucket=bucket, Key=key)
        except:
            raise HTTPInternalServerError
        return response
