import os
import django

# Set up Django environment manually
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from products.models import Category, Product

def seed_db():
    print("Seeding database...")
    Category.objects.all().delete()
    Product.objects.all().delete()

    # Create Categories
    c_electronics = Category.objects.create(name="Tech & Audio", slug="tech-audio")
    c_home = Category.objects.create(name="Home & Decor", slug="home-decor")
    c_accessories = Category.objects.create(name="Accessories", slug="accessories")

    # Create Products
    products = [
        {
            "category": c_electronics,
            "name": "Aura Noise-Canceling Headphones",
            "slug": "aura-headphones",
            "description": "Experience unparalleled acoustic fidelity. The Aura headphones blend intuitive touch controls with a sleek, minimalist design and industry-leading active noise cancellation.",
            "price": "349.99",
            "image_url": "https://images.unsplash.com/photo-1546435770-a3e426bf472b?q=80&w=800&auto=format&fit=crop",
            "stock": 25,
            "available": True
        },
        {
            "category": c_home,
            "name": "Artisan Ceramic Pour-Over Set",
            "slug": "ceramic-pourover",
            "description": "Elevate your morning ritual. Hand-thrown in Kyoto, this matte-finish ceramic pour-over cone and carafe set maintains optimal brewing temperatures.",
            "price": "85.00",
            "image_url": "https://images.unsplash.com/photo-1495474472205-51f4961ee481?q=80&w=800&auto=format&fit=crop",
            "stock": 14,
            "available": True
        },
        {
            "category": c_accessories,
            "name": "Chronos Automatic Watch",
            "slug": "chronos-watch",
            "description": "A study in precision. Featuring a 40mm brushed steel case, sapphire crystal face, and a 42-hour power reserve. Water resistant to 50 meters.",
            "price": "595.00",
            "image_url": "https://images.unsplash.com/photo-1524805444758-089113d48a6d?q=80&w=800&auto=format&fit=crop",
            "stock": 8,
            "available": True
        },
        {
            "category": c_home,
            "name": "Lumina Desk Lamp",
            "slug": "lumina-lamp",
            "description": "Architecturally inspired lighting. The Lumina features tunable color temperature, infinite dimming, and an integrated wireless charging pad in its solid brass base.",
            "price": "129.50",
            "image_url": "https://images.unsplash.com/photo-1507473885765-e6ed057f782c?q=80&w=800&auto=format&fit=crop",
            "stock": 42,
            "available": True
        },
        {
            "category": c_accessories,
            "name": "Nomad Leather Weekender",
            "slug": "nomad-weekender",
            "description": "Engineered for the escape. Crafted from full-grain Italian leather that patinas beautifully over time. Features a dedicated tech compartment and solid brass hardware.",
            "price": "420.00",
            "image_url": "https://images.unsplash.com/photo-1553062407-98eeb64c6a62?q=80&w=800&auto=format&fit=crop",
            "stock": 0,
            "available": True
        },
        {
            "category": c_home,
            "name": "Santal & Vetiver Candle",
            "slug": "santal-candle",
            "description": "Hand-poured coconut wax blend featuring notes of Australian sandalwood, cedarwood, and earthy vetiver. 60-hour burn time.",
            "price": "45.00",
            "image_url": "https://images.unsplash.com/photo-1603006905593-fea5ddbdcdc5?q=80&w=800&auto=format&fit=crop",
            "stock": 110,
            "available": True
        }
    ]

    for p in products:
        Product.objects.create(**p)

    print(f"Successfully created {Category.objects.count()} categories and {Product.objects.count()} products.")

if __name__ == '__main__':
    seed_db()
