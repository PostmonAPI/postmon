from slugify import slugify


def slug(value):
    value = slugify(value, only_ascii=True, spaces=True)
    return value.upper()
