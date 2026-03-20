import boto3
from botocore.exceptions import NoCredentialsError, ClientError


class S3Manager:

    def __init__(self, access_key, secret_key, bucket_name, region="us-east-1"):
        self.bucket_name = bucket_name

        self.s3 = boto3.client(
            "s3",
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region
        )

    # Upload a file to S3
    def upload_file(self, local_file, s3_key):
        try:
            self.s3.upload_file(local_file, self.bucket_name, s3_key)
            print(f"File uploaded: {local_file} -> {s3_key}")

        except FileNotFoundError:
            print("Local file not found")

        except NoCredentialsError:
            print("Invalid AWS credentials")


    # Upload a file and make it publicly accessible
    def upload_file_public(self, local_file, s3_key):
        try:
            self.s3.upload_file(
                local_file,
                self.bucket_name,
                s3_key,
                ExtraArgs={"ACL": "public-read"}
            )

            print(f"Public file uploaded: {local_file} -> {s3_key}")

        except Exception as e:
            print(f"Error: {e}")


    # Download a file from S3
    def download_file(self, s3_key, local_file):
        try:
            self.s3.download_file(self.bucket_name, s3_key, local_file)
            print(f"File downloaded: {s3_key} -> {local_file}")

        except ClientError as e:
            print(f"Error downloading file: {e}")


    # List files inside a bucket or prefix
    def list_files(self, prefix=""):
        try:
            response = self.s3.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix
            )

            if "Contents" not in response:
                print("No files found")
                return []

            files = [obj["Key"] for obj in response["Contents"]]

            for f in files:
                print(f)

            return files

        except ClientError as e:
            print(f"Error listing files: {e}")


    # Delete a file from S3
    def delete_file(self, s3_key):
        try:
            self.s3.delete_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )

            print(f"File deleted: {s3_key}")

        except ClientError as e:
            print(f"Error deleting file: {e}")


    # Generate a temporary URL to access the file
    def generate_presigned_url(self, s3_key, expiration=604800):
        try:
            url = self.s3.generate_presigned_url(
                "get_object",
                Params={
                    "Bucket": self.bucket_name,
                    "Key": s3_key
                },
                ExpiresIn=expiration
            )

            print(f"Generated URL: {url}")
            return url

        except ClientError as e:
            print(f"Error generating URL: {e}")
            return None


    # Get the direct public URL of an object
    def get_public_url(self, s3_key):
        url = f"https://{self.bucket_name}.s3.amazonaws.com/{s3_key}"
        print(f"Public URL: {url}")
        return url


    # Make an existing object publicly accessible
    def make_public(self, s3_key):
        try:
            self.s3.put_object_acl(
                Bucket=self.bucket_name,
                Key=s3_key,
                ACL="public-read"
            )

            print(f"{s3_key} is now public")

        except ClientError as e:
            print(f"Error changing permissions: {e}")

    def upload_fileobj(self, file_obj, s3_key):
        """
        Sube un objeto a S3. No usar ACL, el bucket debe manejar permisos vía Bucket Policy.
        """
        self.s3.upload_fileobj(
            Fileobj=file_obj,
            Bucket=self.bucket_name,
            Key=s3_key,
            ExtraArgs={"ContentType": "image/jpeg", "ContentDisposition": "inline"}
        )
