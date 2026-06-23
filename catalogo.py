from nicegui import ui
import requests
from config import BASE_URL, pb, auth
import json
import io

# --- LOGIN ---
auth()

# --- STATE ---
dynamic_fields = []          #caracteristicas del producto
gallery_files = []           #gallery
main_image_file = None       #img principal

# --- FUNCIONES ---
def add_field():
    dynamic_fields.append({"label": "", "value": ""})
    render_fields.refresh()

def remove_field(index):
    dynamic_fields.pop(index)
    render_fields.refresh()

async def handle_main_upload(e):
    global main_image_file
    try:
        content = await e.file.read()   #img bytes
        main_image_file = {
            "name": e.file.name,
            "type": e.file.content_type if hasattr(e, 'content_type') else 'image/jpeg',
            "content": content
        }
        print(f"MAIN LOADED OK: {e.file.name}")
        ui.notify(f"Imagen principal lista: {e.file.name}", type="positive")
    except Exception as e:
        print(f"Error en handle_main_upload: {e}")
        ui.notify("Error al procesar la imagen principal", type="negative")

async def handle_gallery_upload(e):
    try:
        content = await e.file.read()    #img bytes
        gallery_files.append({
            "name": e.file.name,
            "type": e.file.content_type if hasattr(e, 'content_type') else 'image/jpeg',
            "content": content
        })
        print(f"GALLERY ADDED: {e.file.name}. Total: {len(gallery_files)}")
        ui.notify(f"Añadido a galería: {e.file.name}", type="positive")
    except Exception as e:
        print(f"Error en handle_gallery_upload: {e}")

def save_products():
    #verifica campos vacios
    if not name.value or not price.value:
        ui.notify("Nombre y Precio son obligatorios", type="warning")
        return

    #las caracteristicas del producto se convierten en json
    characteristics_json = json.dumps(dynamic_fields)

    #construccion del data
    data = {
        "nameproduct": str(name.value),
        "price": str(price.value),
        "characteristics": characteristics_json,
        "description": str(description.value)
    }

    #img
    files = []

    #estructura -> (filename, (filename, content, mime_type))
    if main_image_file:
        files.append(
            ("main_image", (main_image_file['name'], main_image_file['content'], main_image_file['type']))
        )

    # Multiples fotos
    for img in gallery_files:
        files.append(
            ("gallery", (img['name'], img['content'], img['type']))
        )

    try:
        headers = {"Authorization": f"Bearer {pb.auth_store.token}"}
        response = requests.post(
            f"{BASE_URL}/api/collections/products/records",
            headers=headers,
            data=data,
            files=files,
            timeout=30
        )

        if response.status_code in [200, 201]:
            ui.notify("Producto e imágenes guardados con éxito", type="positive")
            reset_form()
        else:
            ui.notify(f"Error de PocketBase: {response.text}", type="negative")
    except Exception as e:
        ui.notify(f"Error de red: {e}", type="negative")

def reset_form():
    global main_image_file
    dynamic_fields.clear()
    gallery_files.clear()
    main_image_file = None
    name.value = ""
    price.value = ""
    description.value = ""
    main_upload.reset()
    gallery_upload.reset()
    render_fields.refresh()

def get_product():
    try:
        headers = {"Authorization": f"Bearer {pb.auth_store.token}"}
        response = requests.get(
            f"{BASE_URL}/api/collections/products/records?perPage=200&page=1",
            headers=headers
        )

        if response.status_code == 200:
            return response.json()['items']    #convertimos json -> dicpy, solo extraemos items
        else:
            ui.notify(f"Error cargando productos: {response.text}", type="negative")
            return []
    except Exception as e:
        ui.notify(f"Error {e}", type="negative")
    return []

def show_detail_admin(product):
    images = []

    def file_url(record_id, filename):
        return f"{BASE_URL}/api/files/products/{record_id}/{filename}"

    with ui.dialog() as dialog:
        with ui.card().classes('w-[700px] max-h-[90vh] rounded-xl overflow-y-auto p-0'):

            # --- SECCIÓN IMÁGENES ---
            main_image = product.get("main_image")
            gallery = product.get("gallery", [])

            if main_image:
                images.append(main_image)
            if isinstance(gallery, list):
                images.extend(gallery)

            if images:
                # Ajustamos la altura del carrusel para que no consuma toda la pantalla
                with ui.carousel(animated=True, arrows=True, navigation=True).classes('w-full h-[400px]'):
                    for img in images:
                        with ui.carousel_slide().classes('p-0'):
                            ui.image(file_url(product["id"], img)) \
                                .classes('w-full h-full object-contain bg-gray-100')
            else:
                with ui.column().classes('w-full h-48 items-center justify-center bg-gray-100'):
                    ui.icon('image', size='4rem', color='grey')

            # --- SECCIÓN INFO (El cambio clave aquí) ---
            with ui.column().classes('w-full p-6 gap-4'):
                with ui.row().classes('w-full justify-between items-center'):
                    ui.label(product.get('nameproduct', 'Sin nombre')) \
                        .classes('text-2xl font-bold text-slate-800')
                    ui.label(f"${product.get('price', 0)}") \
                        .classes('text-2xl text-primary font-black')

                ui.separator()

                with ui.column().classes('gap-1'):
                    ui.label('Descripción').classes('text-xs font-bold uppercase text-gray-400')
                    desc = product.get('description')

                    if desc and desc.strip():
                        ui.label(product.get('description', 'Sin descripción')) \
                            .classes('text-gray-700 text-base leading-relaxed')
                    else:
                        ui.label('No hay descripción disponible para el producto') \
                            .classes('text-gray-400 text-sm italic')

                # --- CARACTERISTICAS ---
                raw = product.get("characteristics")
                # Lógica de parseo... (mantén tu lógica de json.loads)
                try:
                    characteristics = json.loads(raw) if isinstance(raw, str) else (raw if raw else [])
                except:
                    characteristics = []

                if characteristics:
                    ui.label('Características Técnicas').classes('text-xs font-bold uppercase text-gray-400 mt-2')
                    with ui.grid(columns=2).classes('w-full gap-2'):
                        for c in characteristics:
                            if isinstance(c, dict):
                                with ui.row().classes('bg-slate-50 p-2 rounded border border-slate-100'):
                                    ui.label(f"{c.get('label')}:").classes('font-bold text-slate-600')
                                    ui.label(f"{c.get('value')}").classes('text-slate-800')

            # Botón de cierre pegado al final
            with ui.row().classes('w-full p-4 sticky bottom-0 bg-white border-t'):
                ui.button("Cerrar", on_click=dialog.close).props('flat').classes('w-full')

    dialog.open()

# --- UI ---
@ui.refreshable
def render_fields():
    for index, field in enumerate(dynamic_fields):
        with ui.row().classes('w-full items-center gap-2 animate-fade-in'):          #crear fila ui
            ui.input(label="Propiedad", placeholder="Ej: Material") \
                .bind_value(field, 'label').classes('flex-grow')                  #conecta el input con dictpy

            ui.input(label="Valor", placeholder="Ej: Madera") \
                .bind_value(field, 'value').classes('flex-grow')

            ui.button(icon="delete", on_click=lambda i=index: remove_field(i)) \
                .props('flat round color=red')

# --- UI ADMIN ---
@ui.page('/admin')
def admin():
    global name, price, description, main_upload, gallery_upload

    # Configuración de estilo global
    ui.colors(primary='#2E5077', secondary='#4DA1A9', accent='#79D7BE')

    #contenedor principal
    with ui.column().classes('w-full items-center bg-slate-50 min-h-screen pb-10'):
        # Header
        with ui.row().classes('w-full justify-center bg-white shadow-sm p-4 mb-6'):
            ui.icon('inventory', size='2rem').classes('text-primary')
            ui.label("Panel de Administración | Palliser").classes('text-2xl font-bold text-slate-800')

        # Formulario principal
        with ui.card().classes('w-full max-w-3xl p-8 shadow-lg rounded-xl'):
            with ui.row().classes('w-full items-center gap-4'):
                ui.label("Información General").classes('text-lg font-bold text-primary')
                ui.separator().classes('flex-grow')

            global name, price, description
            with ui.row().classes('w-full gap-4'):
                name = ui.input("Nombre del Producto").classes('flex-grow') \
                    .props('outlined dense prepend-icon=shopping_bag')

                price = ui.number("Precio", format="%.2f").classes('w-32') \
                    .props('outlined dense prepend-icon=attach_money')

            description = ui.textarea("Descripción del Producto") \
                .classes('w-full').props('outlined dense')

            # Sección de Características Dinámicas
            with ui.row().classes('w-full items-center gap-4 mt-6'):
                ui.label("Características").classes('text-lg font-bold text-primary')
                ui.separator().classes('flex-grow')
                ui.button("Añadir Campo", icon="add", on_click=add_field) \
                    .props('outline size=sm color=secondary')

            with ui.column().classes('w-full bg-slate-50 p-4 rounded-lg border border-dashed border-slate-300'):
                render_fields()

            # Sección de Multimedia
            with ui.row().classes('w-full items-center gap-4 mt-6'):
                ui.label("Multimedia").classes('text-lg font-bold text-primary')
                ui.separator().classes('flex-grow')

            with ui.row().classes('w-full gap-4'):
                with ui.column().classes('flex-grow'):
                    ui.label("Imagen Principal").classes('text-xs font-bold text-gray-500')
                    main_upload = ui.upload(label="Foto Principal", on_upload=handle_main_upload) \
                        .props('accept=image/* max-files=1 auto-upload').classes('w-full flex-grow')

                with ui.column().classes('flex-grow'):
                    ui.label("Galería").classes('text-xs font-bold text-gray-500')
                    gallery_upload = ui.upload(label="Galería (Múltiple)", on_upload=handle_gallery_upload) \
                        .props('accept=image/* multiple auto-upload').classes('w-full flex-grow')

            with ui.row().classes('w-full justify-end mt-8 gap-4'):
                # Botón de Acción
                ui.button('Ver registros', icon="list", on_click=lambda: ui.navigate.to('/productos')) \
                    .classes('px-6 shadow-md').props('flat color=grey')

                ui.button("Limpiar", icon="restart_alt", on_click=reset_form) \
                    .props('flat color=grey')

                ui.button("Guardar Producto", icon="save", on_click=save_products) \
                    .classes('px-6 shadow-md').props('color=primary size=lg')

@ui.page('/productos')
def productos():
    ui.colors(primary='#2E5077', secondary='#4DA1A9', accent='#79D7BE')

    #contenedor principal
    with ui.column().classes('w-full items-center bg-slate-50 min-h-screen pb-10'):
        # Header
        with ui.row().classes('w-full justify-center bg-white shadow-sm p-4 mb-6'):
            ui.icon('inventory', size='2rem').classes('text-primary')
            ui.label("Productos Registrados | Palliser").classes('text-2xl font-bold text-slate-800')
            ui.button('Volver', icon="back", on_click=lambda: ui.navigate.to('/admin')) \
                .props('flat color=primary').classes('self-end mb-4')

        with ui.card().classes('w-full max-w-7xl p-6 shadow-lg rounded-xl'):
            #carga de datos
            products = get_product()

            #validacion de datos
            if not products:
                with ui.column().classes('w-full items-center py-10'):
                    ui.icon('remove_shopping_cart', size='5rem').classes('text-gray-500')
                    ui.label('No existen productos').classes('text-xl text-gray-500')
                return

            #grid principal
            with ui.grid(columns=3).classes('w-full gap-8'):
                for product in products:          #iteramos cada producto
                    # -- img ---
                    main_image = product.get("main_image")

                    def file_url(record_id, filename):
                        return f"{BASE_URL}/api/files/products/{record_id}/{filename}"

                    #card
                    with ui.card().classes(
                            'w-full flex flex-col p-0 rounded-2xl overflow-hidden shadow-sm'
                            'border border-gray-200 hover:shadow-xl transition-all duration-300 bg-white cursor-pointer'
                            'bg-white  cursor-pointer'
                    ).on('click', lambda _, p=product: show_detail_admin(p)):

                        with ui.column().classes('w-full h-48 bg-gray-100 relative overflow-hidden'):
                            if main_image:
                                ui.image(file_url(product["id"], main_image)) \
                                    .classes('w-full h-full object-cover')
                            else:
                                with ui.column().classes('w-full h-full items-center justify-center text-gray-300'):
                                    ui.icon('image', size='4rem')

                        #informacion del producto
                        with ui.column().classes('p-5 flex-grow gap-2'):
                            with ui.row().classes('w-full justify-between items-start no-wrap'):
                                ui.label(product.get('nameproduct', 'Sin nombre')) \
                                    .classes('text-lg font-bold text-slate-800 leading-tight flex-grow')

                                ui.label(f"${product.get('price', '0')}") \
                                    .classes('text-lg font-bold text-slate-800 leading-tight flex-grow')

                            ui.separator().classes('my-1 opacity-50')

                            with ui.column().classes('gap-1'):
                                ui.label('Descripción').classes('text-xs font-bold uppercase text-gray-400')
                                desc = product.get('description')

                                if desc and desc.strip():
                                    ui.label(product.get('description', 'Sin descripción')) \
                                        .classes('text-gray-700 text-base leading-relaxed')
                                else:
                                    ui.label('No hay descripción disponible para el producto') \
                                        .classes('text-gray-400 text-sm italic')

                            #caracteristicas
                            with ui.column().classes('w-full mt-auto'):
                                raw_characteristics = product.get("characteristics")
                                characteristics = []

                                try:
                                    #si viene como string json -> listapy
                                    if isinstance(raw_characteristics, str):
                                        characteristics = json.loads(raw_characteristics)
                                    #ya viene como listapy
                                    elif isinstance(raw_characteristics, list):
                                        characteristics = raw_characteristics
                                except:
                                    characteristics = []

                                if characteristics:
                                    ui.label('Caracteristicas').classes('text-[14px] font-bold text-gray-400 uppercase mt-2 mb-1')

                                    # --- PRIMERA FILA (máx 3) ---
                                    with ui.grid(columns=2).classes('w-full gap-2'):
                                        for c in characteristics:
                                            with ui.row().classes(
                                                    'bg-slate-50 rounded-lg px-2 py-1 border border-slate-200 items-center justify-between no-wrap'
                                            ):
                                                ui.label(f"{c.get('label', '')}:").classes(
                                                    'text-[12px] font-bold text-slate-500 uppercase truncate')
                                                ui.label(c.get('value', '')).classes(
                                                    'text-[12px] font-medium text-slate-700 truncate')

@ui.page('/')
def home():
    ui.navigate.to('/admin')



if __name__ in {"__main__", "__mp_main__"}:
    ui.run(title="Catalogo | Palliser", port=8080, host='0.0.0.0')

    #172.21.211.76:8080