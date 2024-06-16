# PetNet
## Preparacion del ambiente de trabajo
Para poder compilar el proyecto primero debes tener Python Instalado [Descarga Aqui](https://www.python.org/downloads/) la versión recomendada y usada en el proyecto es python 3.12.

Una vez instalado python y el proyecto descargado, deberas de utilizar el siguiente comando:
```
pip install virtualenv
```
Este paquete nos permitira crear ambientes virtuales de trabajo, luego utilizamos
```
python virtualenv -m env
```
Para poder crear la carpeta de env donde se guardara los nuevos paquetes a instalar, para poder activar este ambiente virtual deberas de utilizar, en la terminal:
``` 
.\env\Scripts\activate
```

Una vez activada el ambiente virtual utilizamos,esto descargara todos los paquetes necesarios para compilar:
```
pip install -r requirements.txt
```
Recordar para poder realizar esta compilación debes de tener:

* Mysql instalado previamente
* IDE ( Visual Studio(recomendacion) )
* Python 3.12
* Archivo .env que contenga
    * CONFIGURATION="development"
    * SECRET_KEY = "random_text_key"
    * DATABASE_URL="postgresql://postgres:root@localhost:5432/db_petnet_test"
    * MAIL_USERNAME = "user@gmail.com"
    * MAIL_PASSWORD = "generate_password"

Teniendo todos los requisitos previos recordar crear un Schema o Database llamado **db_petnet_test**, para poder compilar las versiones de migrations:


```
flask db upgrade
```
Teniendo todos los upgrade previos de la base de datos podras utilizar:
```
flask run
```
De esta manera ya podras correr el proyecto y tener acceso a los endpoint.
