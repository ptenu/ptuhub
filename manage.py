import click
from cli.contacts import create_contact, set_password, import_from_stripe
from cli import address
from model.File import File


@click.group()
def cli():
    pass


@cli.command()
def test():
    click.echo("Worked.")


@cli.command()
def import_addr():
    click.echo("Downloading data...")
    address.download()

    click.echo(click.style("Download complete", fg="green"))
    click.echo("Importing (this may take a while!")
    address.do_import()


@cli.command()
def stripe_import():
    click.echo("Importing Stripe.com customers...")
    imported, skipped = import_from_stripe()
    click.echo("Done")
    click.echo(f"Imported:     {str(imported)}")
    click.echo(f"Skipped:      {str(skipped)}")


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
