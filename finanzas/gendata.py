"""Generate fake financial data for testing the dashboard."""

import random
from datetime import datetime, timedelta

import pandas as pd

# Define categories and their subcategories with typical concepts
CATEGORIES = {
    "Vivienda": {
        "Alquiler": ["Alquiler piso", "Fianza"],
        "Suministros": ["Luz", "Agua", "Gas", "Internet"],
        "Mantenimiento": ["Reparación", "Limpieza", "Muebles"],
    },
    "Alimentación": {
        "Supermercado": ["Mercadona", "Carrefour", "Lidl", "Dia"],
        "Restaurantes": ["Restaurante", "Bar", "Cafetería"],
        "Comida para llevar": ["Glovo", "Uber Eats", "Just Eat"],
    },
    "Transporte": {
        "Público": ["Metro", "Bus", "Taxi"],
        "Privado": ["Gasolina", "Parking", "Mantenimiento coche"],
    },
    "Ocio": {
        "Entretenimiento": ["Cine", "Teatro", "Conciertos"],
        "Deportes": ["Gimnasio", "Material deportivo"],
        "Viajes": ["Vuelos", "Hotel", "Actividades"],
    },
    "Suscripciones": {
        "Streaming": ["Netflix", "Spotify", "HBO"],
        "Software": ["Adobe", "Microsoft", "iCloud"],
    },
    "Ingresos": {
        "Nómina": ["Nómina", "Paga extra"],
        "Otros": ["Devolución", "Regalo", "Reembolso"],
    },
}

# Define typical amounts for each category
AMOUNT_RANGES = {
    "Vivienda": (-1200, -400),
    "Alimentación": (-500, -20),
    "Transporte": (-200, -10),
    "Ocio": (-300, -15),
    "Suscripciones": (-50, -5),
    "Ingresos": (1000, 3000),
}


def generate_transactions(
    start_date: datetime,
    end_date: datetime,
    initial_balance: float = 5000.0,
    num_transactions_per_day: tuple[int, int] = (1, 5),
) -> pd.DataFrame:
    """Generate fake transactions for the given date range."""
    transactions = []
    current_balance = initial_balance
    current_date = start_date

    while current_date <= end_date:
        # Generate random number of transactions for this day
        num_transactions = random.randint(*num_transactions_per_day)

        for _ in range(num_transactions):
            # Select random category and subcategory
            category = random.choice(list(CATEGORIES.keys()))
            subcategory = random.choice(list(CATEGORIES[category].keys()))
            concept = random.choice(CATEGORIES[category][subcategory])

            # Generate amount based on category
            min_amount, max_amount = AMOUNT_RANGES[category]
            amount = round(random.uniform(min_amount, max_amount), 2)

            # Update balance
            current_balance += amount

            transactions.append(
                {
                    "Fecha": current_date,
                    "Concepto": concept,
                    "Category": category,
                    "Subcategory": subcategory,
                    "Importe": amount,
                    "Saldo": round(current_balance, 2),
                }
            )

        current_date += timedelta(days=1)

    return pd.DataFrame(transactions)


def main() -> None:
    """Generate fake data and save it to CSV."""
    # Generate 6 months of data
    end_date = datetime.now()
    start_date = end_date - timedelta(days=180)

    df = generate_transactions(
        start_date=start_date,
        end_date=end_date,
        initial_balance=5000.0,
        num_transactions_per_day=(1, 5),
    )

    # Sort by date
    df = df.sort_values("Fecha")

    # Save to CSV
    output_path = "./data/fake_dataset.csv".format()
    df.to_csv(output_path, index=False)
    print(f"Generated {len(df)} transactions and saved to {output_path}")
    print(f"Date range: {df['Fecha'].min()} to {df['Fecha'].max()}")
    print(f"Final balance: {df['Saldo'].iloc[-1]:,.2f}€")


if __name__ == "__main__":
    main()
