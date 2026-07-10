import click

from src.exceptions import ValidationError
from src.modules.administrar.user.logic import crear_usuario


def registrar_comandos(app):
    app.cli.add_command(create_it)


@click.command("create-it")
@click.option("--username", prompt="Usuario")
@click.option("--password", prompt="Contraseña", hide_input=True, confirmation_prompt=True)
def create_it(username, password):
    """Crea el primer usuario IT (bootstrap), sin depender de la UI.

    Necesario porque /usuarios/nuevo ya exige estar logueado como IT/BackOffice.
    Sin vincular a ningún empleado; se puede linkear después desde /usuarios.
    """
    try:
        id_usuario = crear_usuario(username=username, password=password, role="IT")
    except ValidationError as error:
        raise click.ClickException(str(error))

    click.echo(f"Usuario IT '{username}' creado con id {id_usuario}.")
