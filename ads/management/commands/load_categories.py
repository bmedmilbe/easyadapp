# ads/management/commands/load_categories.py
from ads.models import Category
from django.core.management.base import BaseCommand
from django.utils.text import slugify


class Command(BaseCommand):
    help = 'Load initial categories into the database'

    def handle(self, *args, **options):
        categories = [
            {"name": "Carros", "icon": "🚗"},
            {"name": "Motorizadas", "icon": "🏍️"},
            {"name": "Bicicletas", "icon": "🚲"},
            {"name": "Barcos", "icon": "🚤"},
            {"name": "Peças e acessórios", "icon": "🔧"},
            {"name": "Casas", "icon": "🏠"},
            {"name": "Apartamentos", "icon": "🏢"},
            {"name": "Terrenos", "icon": "🏗️"},
            {"name": "Espaços comerciais", "icon": "🏪"},
            {"name": "Telemóveis", "icon": "📱"},
            {"name": "Computadores", "icon": "💻"},
            {"name": "Tablets", "icon": "📱"},
            {"name": "Televisões", "icon": "📺"},
            {"name": "Consolas", "icon": "🎮"},
            {"name": "Acessórios", "icon": "🔌"},
            {"name": "Móveis", "icon": "🛋️"},
            {"name": "Frigoríficos", "icon": "🧊"},
            {"name": "Fogões", "icon": "🔥"},
            {"name": "Máquinas de lavar", "icon": "🧺"},
            {"name": "Decoração", "icon": "🎨"},
            {"name": "Roupa", "icon": "👕"},
            {"name": "Calçado", "icon": "👟"},
            {"name": "Malas", "icon": "🧳"},
            {"name": "Relógios", "icon": "⌚"},
            {"name": "Joias", "icon": "💎"},
            {"name": "Brinquedos", "icon": "🧸"},
            {"name": "Carrinhos", "icon": "🛒"},
            {"name": "Artigos para bebé", "icon": "👶"},
            {"name": "Ferramentas", "icon": "🔨"},
            {"name": "Máquinas", "icon": "⚙️"},
            {"name": "Produtos agrícolas", "icon": "🌾"},
            {"name": "Equipamentos de pesca", "icon": "🎣"},
            {"name": "Materiais de construção", "icon": "🧱"},
            {"name": "Tintas", "icon": "🎨"},
            {"name": "Equipamentos", "icon": "🛠️"},
            {"name": "Cães", "icon": "🐕"},
            {"name": "Gatos", "icon": "🐈"},
            {"name": "Galinhas", "icon": "🐔"},
            {"name": "Cabras", "icon": "🐐"},
            {"name": "Porcos", "icon": "🐖"},
            {"name": "Gado", "icon": "🐄"},
            {"name": "Frutas", "icon": "🍎"},
            {"name": "Legumes", "icon": "🥬"},
            {"name": "Cacau", "icon": "🍫"},
            {"name": "Café", "icon": "☕"},
            {"name": "Pimenta", "icon": "🌶️"},
            {"name": "Mel", "icon": "🍯"},
            {"name": "Peixe", "icon": "🐟"},
            {"name": "Marisco", "icon": "🦞"},
            {"name": "Equipamentos de escritório", "icon": "📠"},
            {"name": "Equipamentos de restauração", "icon": "🍽️"},
            {"name": "Ferramentas profissionais", "icon": "🔧"},
            {"name": "Equipamento desportivo", "icon": "⚽"},
            {"name": "Instrumentos musicais", "icon": "🎵"},
            {"name": "Jogos", "icon": "🎲"},
            {"name": "Livros", "icon": "📚"},
            {"name": "Material escolar", "icon": "✏️"},
            {"name": "Outros", "icon": "🎁"},
        ]

        for category in categories:
            obj, created = Category.objects.get_or_create(
                name=category["name"],
                defaults={
                    "slug": slugify(category["name"]),
                    "icon": category["icon"],
                    "description": f"Produtos da categoria {category['name']}"
                }
            )
            if created:
                self.stdout.write(f"✅ Created category: {category['icon']} {category['name']}")
            else:
                self.stdout.write(f"⏭️  Category already exists: {category['icon']} {category['name']}")