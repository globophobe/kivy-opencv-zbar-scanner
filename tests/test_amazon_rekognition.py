import boto3


class RekognitionTestClient(object):
    def __init__(self, source='young-luke.jpg', target='old-luke.jpg'):
        self.client = boto3.client(
            'rekognition',
            aws_access_key_id=None,
            aws_secret_access_key=None,
            region_name=None,
        )
        self.source = source
        self.target = target

    def get_image_data(self, path):
        with open(path, 'rb') as image:
            return image.read()

    def compare_faces(self):
        return self.client.compare_faces(
            SimilarityThreshold=0,
            SourceImage={'Bytes': self.get_image_data(self.source)},
            TargetImage={'Bytes': self.get_image_data(self.target)})


if __name__ == '__main__':
    client = RekognitionTestClient()
    result = client.compare_faces()
    print(result)
