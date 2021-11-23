import cognitive_face as cf


def test_cognitive():
    base_url = 'https://westcentralus.api.cognitive.microsoft.com/face/v1.0/'
    key = None

    cf.BaseUrl.set(base_url)
    cf.Key.set(key)

    img = open('young-luke.jpeg', 'rb')
    return cf.face.detect(img)


if __name__ == '__main__':
    response = test_cognitive()
    print(response)
