import click

from src.exceptions import ValidationError
from src.modules.administrar.user.logic import crear_usuario


def registrar_comandos(app):
    app.cli.add_command(create_admin)


@click.command("create-admin")
@click.option("--name", prompt="Nombre")
@click.option("--last-name", prompt="Apellido")
@click.option("--dni", prompt="DNI")
@click.option("--username", prompt="Usuario")
@click.option("--password", prompt="Contraseña", hide_input=True, confirmation_prompt=True)
def create_admin(name, last_name, dni, username, password):
    """Crea el primer usuario Admin (bootstrap), sin depender de la UI.

    Necesario porque /user/nuevo ya exige estar logueado como Admin/BackOffice.
    """
    try:
        id_usuario = crear_usuario(
            name=name, last_name=last_name, dni=dni,
            username=username, password=password, role="Admin",
        )
    except ValidationError as error:
        raise click.ClickException(str(error))

    click.echo(f"Admin '{username}' creado con id {id_usuario}.")
