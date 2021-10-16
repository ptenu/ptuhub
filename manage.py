import click
from cli.contacts import create_contact


@click.group()
def cli():
    pass


@cli.command()
def test():
    click.echo("Worked.")


@cli.command()
@click.option("--given_name")
@click.option("--family_name")
@click.option("--email")
def add_contact(given_name, family_name, email):
    """
    Add a new contact
    """
    create_contact(given_name, family_name, email)
    click.echo("Contact added to database")


if __name__ == "__main__":
    cli()
