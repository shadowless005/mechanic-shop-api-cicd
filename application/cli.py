"""Explicit local administrator commands; no public role-granting endpoint."""
import click
from flask.cli import with_appcontext
from sqlalchemy import select
from werkzeug.security import generate_password_hash

from application.extensions import db, cache
from application.models import Customer


@click.command('create-staff')
@click.option('--email', required=True, help='New disposable staff account email.')
@click.option('--phone', required=True, help='Unique demo phone number.')
@click.password_option(help='Password for the new staff account.')
@with_appcontext
def create_staff(email, phone, password):
    """Create a NEW staff account from a trusted terminal."""
    if not password:
        raise click.ClickException('Password cannot be empty.')
    existing = db.session.execute(select(Customer).where(
        (Customer.email == email) | (Customer.phone == phone)
    )).scalars().first()
    if existing:
        raise click.ClickException('Email or phone already exists. Choose a new demo identity; no account was changed.')
    staff = Customer(name='Demo Staff', email=email, phone=phone,
                     address='Demo Shop', password=generate_password_hash(password), is_staff=True)
    db.session.add(staff)
    db.session.commit()
    cache.clear()
    click.echo(f'Created staff account: {email}. Log in through POST /customers/login.')


@click.command('upgrade-db')
@with_appcontext
def upgrade_db():
    """Create missing tables and add the staff column without deleting data."""
    from sqlalchemy import inspect, text
    db.create_all()
    columns = {column['name'] for column in inspect(db.engine).get_columns('customers')}
    if 'is_staff' not in columns:
        with db.engine.begin() as connection:
            connection.execute(text(
                'ALTER TABLE customers ADD COLUMN is_staff BOOLEAN NOT NULL DEFAULT FALSE'
            ))
        click.echo('Added is_staff; existing customers remain regular customers.')
    else:
        click.echo('Database schema is current.')
    click.echo('Existing passwords are unchanged. Reset legacy plaintext accounts before using them.')


@click.command('reset-password')
@click.option('--email', required=True)
@click.password_option()
@with_appcontext
def reset_password(email, password):
    """Set a hashed password for an existing account from a trusted terminal."""
    if not password:
        raise click.ClickException('Password cannot be empty.')
    customer = db.session.execute(select(Customer).where(Customer.email == email)).scalar_one_or_none()
    if customer is None:
        raise click.ClickException('Customer not found; nothing changed.')
    customer.password = generate_password_hash(password)
    db.session.commit()
    click.echo('Password reset. The account role was not changed.')
