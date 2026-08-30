from typing import List
from sqlalchemy.orm import Mapped, mapped_column
from application.extensions import db


service_ticket_mechanic = db.Table(
    "service_ticket_mechanic",
    db.Column(
        "service_ticket_id",
        db.ForeignKey("service_tickets.id"),
        primary_key=True
    ),
    db.Column(
        "mechanic_id",
        db.ForeignKey("mechanics.id"),
        primary_key=True
    )
)

service_ticket_inventory = db.Table(
    "service_ticket_inventory",
    db.Column(
        "service_ticket_id",
        db.ForeignKey("service_tickets.id"),
        primary_key=True
    ),
    db.Column(
        "inventory_id",
        db.ForeignKey("inventory.id"),
        primary_key=True    
    )    
)


class Customer(db.Model):
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(db.String(255), nullable=False)
    email: Mapped[str] = mapped_column(db.String(360), unique=True, nullable=False)
    phone: Mapped[str] = mapped_column(db.String(20), unique=True, nullable=False)
    address: Mapped[str] = mapped_column(db.String(255), nullable=False)
    password: Mapped[str] = mapped_column(db.String(255), nullable=False)

    service_tickets: Mapped[List["ServiceTicket"]] = db.relationship(
        back_populates="customer"
    )

    def __repr__(self) -> str:
        return f"<Customer {self.name}>"


class Mechanic(db.Model):
    __tablename__ = "mechanics"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(db.String(255), nullable=False)
    email: Mapped[str] = mapped_column(db.String(360), unique=True, nullable=False)
    phone: Mapped[str] = mapped_column(db.String(20), unique=True, nullable=False)
    address: Mapped[str] = mapped_column(db.String(255), nullable=False)
    salary: Mapped[float] = mapped_column(db.Float, nullable=False)

    service_tickets: Mapped[List["ServiceTicket"]] = db.relationship(
        secondary=service_ticket_mechanic,
        back_populates="mechanics"
    )

    def __repr__(self) -> str:
        return f"<Mechanic {self.name}>"


class Inventory(db.Model):
    __tablename__ = "inventory"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(db.String(255), nullable=False)
    price: Mapped[float] = mapped_column(db.Float, nullable=False)

    service_tickets: Mapped[List["ServiceTicket"]] = db.relationship(
        secondary=service_ticket_inventory,
        back_populates="inventory"
    )

    def __repr__(self) -> str:
        return f"<Inventory {self.name}>"


class ServiceTicket(db.Model):
    __tablename__ = "service_tickets"

    id: Mapped[int] = mapped_column(primary_key=True)

    description: Mapped[str] = mapped_column(
        db.String(500),
        nullable=False
    )

    vin: Mapped[str] = mapped_column(
        db.String(17),
        nullable=False
    )

    customer_id: Mapped[int] = mapped_column(
        db.ForeignKey("customers.id"),
        nullable=False
    )

    customer: Mapped["Customer"] = db.relationship(
        back_populates="service_tickets"
    )

    mechanics: Mapped[List["Mechanic"]] = db.relationship(
        secondary=service_ticket_mechanic,
        back_populates="service_tickets"
    )

    inventory: Mapped[List["Inventory"]] = db.relationship(
        secondary=service_ticket_inventory,
        back_populates="service_tickets"
    )

    def __repr__(self) -> str:
        return f"<ServiceTicket {self.id}>"


