import client

session = client.SearchSession()

session.get_captcha()
session.check_captcha(input('Введите каптчу: '))
obj = session.get_info(input('Введите кадастровый номер: '))
print(obj)
