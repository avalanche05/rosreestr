import client

session = client.SearchSession()

session.get_captcha()
obj = session.get_list_by('Чистые пруды канаш')
print(obj)
