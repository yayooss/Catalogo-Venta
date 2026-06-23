from nicegui import ui
from config import BASE_URL, pb, auth
import requests
import json

# --- LOGIN ---
auth()

# --- STATE ---
products = []       #productos traidos del backend
search_text = ""    #texto del buscador
cart = []           #carrito del usuario

# --- GET DATA ---
def get_products():
    try:
        headers = {"Authorization": f"Bearer {pb.auth_store.token}"}      #authentication
        response = requests.get(f"{BASE_URL}/api/collections/products/records?perPage=200&page=1", headers=headers)
        data = response.json()         #la respuesta de pb, se convierte en un diccionario py
        if response.status_code == 200:
            return data['items']      #solo extrae la lista de productos
    except Exception as e:
        ui.notify(f"Error de conexion: {e}", type="negative")
    return []

# --- CART LOGIC ---
def add_to_cart(product):                    #product -> id,nameproduct, price, description, main_image, characteristics
    for item in cart:       #se revisa si el producto ya existe en el carrito
        if item['id'] == product['id']:      #aqui se hace la verificacion
            item['qty'] += 1                 #si ya existe, incrementa
            ui.notify(f"{product['nameproduct']} añadido al carrito", icon="shopping_cart", type="positive")
            render_cart.refresh()            #actualiza ui
            return

    #Si no existe en el carrito
    product_copy = product.copy()           #crea una copia para evitar modificar el original
    product_copy['qty'] = 1                 #qty inicial
    cart.append(product_copy)               #se mete al carrito

    ui.notify(f"{product['nameproduct']} añadido al carrito", icon="shopping_cart", type="positive")
    render_cart.refresh()                   #actualiza ui

# --- REMOVE CART ---
def remove_from_cart(index):               #index es la posicion del producto a eliminar
    removed = cart.pop(index)              #elimina un producto usando su posicion - indice
    ui.notify(f"{removed['nameproduct']} eliminado", type="warning")
    render_cart.refresh()                  #actualiza ui

# --- SEND ---
def send_interest(data):         #en data se envio el email y el phone
    #Si cualquiera de los campos esta vacío, se envia msj de error
    if not data["email"] or not data["phone"]:
        ui.notify("Completa todos los campos", type="warning")
        return

    try:
        payload = build_payload(data)          #se convierte los datos en un json listo para enviar. En json=payload esta toda la info del post

        #envio de post
        response = requests.post(f"{BASE_URL}/api/collections/interests/records", json=payload, headers={"Content-Type": "application/json"})

        print("STATUS:", response.status_code)
        print("RESPONSE:", response.text)

        if response.status_code == 200:
            ui.notify("Pronto nos comunicaremos con usted, gracias por el interés.", type="positive", duration=4000)
            cart.clear()              #se vacia carrito
            render_cart.refresh()     #actualiza ui
        else:
            ui.notify("Error al enviar solicitud", type="negative")
            print("RESPONSE ERROR:", response.text)
    except Exception as e:
        ui.notify(f"Error: {e}", type="negative")

# --- DETAILS PRODUCT ---
# --- DETAILS PRODUCT ---
def show_detail(product):
    """
    product contiene:
    id,
    nameproduct,
    price,
    description,
    main_image,
    characteristics
    """

    images = []

    # =====================================================
    # URL DE IMAGEN
    # =====================================================

    def file_url(record_id, filename):
        """
        Construye la URL de la imagen
        """
        return f"{BASE_URL}/api/files/products/{record_id}/{filename}"

    # =====================================================
    # MODAL
    # =====================================================

    with ui.dialog() as dialog, ui.card().classes(
        'w-[700px] max-h-[90vh] rounded-xl overflow-y-auto p-0'
    ):

        # =================================================
        # SECCIÓN IMÁGENES
        # =================================================

        main_image = product.get("main_image")
        gallery = product.get("gallery", [])

        # Imagen principal
        if main_image:
            images.append(main_image)

        # Galería adicional
        if isinstance(gallery, list):
            images.extend(gallery)

        # =================================================
        # CARRUSEL
        # =================================================

        if images:

            # Carrusel con altura vertical grande
            with ui.carousel(
                animated=True,
                arrows=True,
                navigation=True
            ).classes(
                'w-full h-[650px] bg-gray-100'
            ):

                for img in images:
                    with ui.carousel_slide().classes(
                            'p-0 flex items-center justify-center bg-gray-100'
                    ):
                        ui.image(
                            file_url(product["id"], img)
                        ).classes(
                            'max-h-full max-w-full object-contain'
                        )

        else:

            with ui.column().classes(
                'w-full h-48 justify-center items-center bg-gray-100'
            ):

                ui.icon(
                    'image',
                    size='4rem',
                    color='gray'
                )

        # =================================================
        # CONTENIDO
        # =================================================

        with ui.column().classes(
            'w-full p-6 gap-4'
        ):

            # =================================================
            # HEADER
            # =================================================

            with ui.row().classes(
                'w-full justify-between items-center'
            ):

                ui.label(
                    product.get(
                        'nameproduct',
                        'Sin nombre'
                    )
                ).classes(
                    'text-2xl font-bold text-slate-800'
                )

                ui.label(
                    f"${product.get('price', 0)}"
                ).classes(
                    'text-2xl text-primary font-black'
                )

            ui.separator()

            # =================================================
            # DESCRIPCIÓN
            # =================================================

            with ui.column().classes('gap-1'):

                ui.label(
                    'Descripción:'
                ).classes(
                    'text-xs font-bold uppercase text-gray-400'
                )

                desc = product.get('description')

                if desc and desc.strip():

                    ui.label(desc).classes(
                        'text-gray-700 text-base leading-relaxed'
                    )

                else:

                    ui.label(
                        'No hay descripción disponible para el producto'
                    ).classes(
                        'text-gray-400 text-sm italic'
                    )

            # =================================================
            # CARACTERÍSTICAS
            # =================================================

            raw = product.get("characteristics")

            try:

                characteristics = (
                    json.loads(raw)
                    if isinstance(raw, str)
                    else (raw if raw else [])
                )

            except:

                characteristics = []

            if characteristics:

                ui.label(
                    'Características Técnicas'
                ).classes(
                    'text-xs font-bold uppercase text-gray-400 mt-2'
                )

                with ui.grid(columns=2).classes(
                    'w-full gap-2'
                ):

                    for c in characteristics:

                        if isinstance(c, dict):

                            with ui.row().classes(
                                'bg-slate-50 p-2 rounded '
                                'border border-slate-100 items-center'
                            ):

                                ui.label(
                                    f"{c.get('label')}:"
                                ).classes(
                                    'font-bold text-slate-600'
                                )

                                ui.label(
                                    f"{c.get('value')}"
                                ).classes(
                                    'text-slate-800'
                                )

        # =================================================
        # BOTONES
        # =================================================

        with ui.column().classes(
            'w-full p-4 sticky bottom-0 bg-white border-t'
        ):

            # =============================================
            # BOTÓN AGREGAR
            # =============================================

            ui.button(
                "Añadir al carrito",
                icon="add_shopping_cart",
                on_click=lambda: [
                    add_to_cart(product),
                    dialog.close()
                ]
            ).classes(
                'w-full py-3'
            ).props(
                'color=primary'
            )

            # =============================================
            # BOTÓN CERRAR
            # =============================================

            ui.button(
                "Cerrar",
                on_click=dialog.close
            ).props(
                'flat'
            ).classes(
                'w-full'
            )

    # =====================================================
    # ABRIR MODAL
    # =====================================================

    dialog.open()




# --- Se prepara el formato JSON listo para enviar a la BD ---
def build_payload(data):            #recibe email, phone
    items = [
        {
            "nameproduct": i["nameproduct"],
            "price": float(i["price"]),     #se hace la conversion a float porque a veces se envia como str
            "qty": i["qty"]
        }
        for i in cart   #en cart esta lla info de nameproduct,price,qty
    ]

    #calculo del total
    total = sum(i["price"] * i["qty"] for i in items)

    return {
        "email": data["email"],     #se mantiene el correo
        "phone": data["phone"],     #se mantiene el phone
        "items": items,             #se envia los items formato json, que se realizo aqui
        "total": total              #se envia el total, realizado aqui
    }


# --- CARTA -> IMG, TITLE, PRICE, ICON CARRITO ---
@ui.refreshable
def render_grid():
    with ui.grid(columns=3).classes('w-full gap-6'):   #cuadricula, 3 columnas fijas
        for product in products:
            #si hay search_text y no coincide con el nombre del producto, se ignora. si existe coincidencia se muestra
            if search_text and search_text.lower() not in product.get('nameproduct', '').lower():
                continue

            #se crea una card. cada producto es una card
            with ui.card().classes('rounded-xl overflow-hidden shadow hover:shadow-xl transition'):
                #funcion para construir la url de img
                def file_url(record_id, filename):
                    return f"{BASE_URL}/api/files/products/{record_id}/{filename}"

                main_image = product.get("main_image")
                with ui.column().classes('w-full h-48 p-2 bg-gray-100 relative overflow-hidden'):
                    if main_image:
                        ui.image(file_url(product["id"], main_image)) \
                            .classes('w-full h-full object-cover cursor-pointer rounded-lg shadow-sm') \
                            .on('click', lambda _, p=product: show_detail(p))
                    else:
                        with ui.column().classes('w-full h-full items-center justify-center text-gray-300'):
                            ui.icon('image', size='4rem')

                #contenido de la card
                with ui.column().classes('p-5 flex-grow w-full'):
                    ui.label(product.get('nameproduct', 'Sin nombre')) \
                        .classes('text-lg font-bold text-slate-800 leading-tight no-wrap')
                    ui.label(f"${product.get('price', 0)}").classes('text-lg font-bold text-slate-800 leading-tight flex-grow')

                    #boton del carrito
                    ui.button(icon='add_shopping_cart', on_click=lambda p=product: add_to_cart(p)) \
                        .props('flat round color=primary').classes('self-end')

# --- SECCION DEL CARRITO ---
@ui.refreshable
def render_cart():
    #si la lista esa vacia, muestra mensaje
    if not cart:
        with ui.column().classes('w-full items-center py-10'):
            ui.icon('remove_shopping_cart', size='5rem').classes('text-gray-500')
            ui.label('Tu carrito esta vacio').classes('text-xl text-gray-500')
        return

    #layout principal
    with ui.row().classes('w-full gap-6'):
        #lista de productos en el carrito
        with ui.column().classes('flex-grow'):
            #index -> posicion del producto
            #item -> producto
            #enumerate(cart) -> (indice,elemento)
            for index, item in enumerate(cart):
                with ui.card().classes('w-full p-4 mb-2 cursor-pointer hover:bg-gray-50') \
                        .on('click', lambda  _, p=item: show_detail(p)):
                    with ui.row().classes('w-full items-center justify-between'):
                        #informacion del producto
                        with ui.column():
                            ui.label(item['nameproduct']).classes('font-bold')
                            ui.label(f"${item['price']}").classes('text-primary')

                        # --- CANTIDAD ---
                        ui.label(f"x{item['qty']}").classes('text-lg font-bold text-gray-600')

                        # --- DELETE ---
                        ui.button(
                            icon='delete',
                            on_click=lambda i=index: remove_from_cart(i)
                        ).props('flat round color=red')

        #panel derecho
        with ui.card().classes('w-80 p-6 h-fit bg-slate-50'):
            ui.label('RESUMEN').classes('text-lg font-bold mb-2')
            total = sum(float(item['price']) * item['qty'] for item in cart)
            ui.label(f"Total: ${total:,.2f}").classes('text-xl font-bold text-primary mb-4')

            #formulario dinamico
            interest_container = ui.column().classes('w-full gap-3')

            with interest_container:
                btn_interest = ui.button('ESTOY INTERESADO', icon='contact_mail')\
                    .classes('w-full py-4').props('color=secondary')

                #funcion para mostrar el formulario
                def show_fields():
                    btn_interest.set_visibility(False)    #oculta el boton y se reemplaza con el formulario
                    with interest_container:
                        email = ui.input('Correo electronico').classes('w-full').props('outlined')
                        phone = ui.input('Telefono').classes('w-full').props('outlined')
                        ui.button('ENVIAR SOLICITUD',
                                    on_click=lambda: send_interest({
                                        'email': email.value,
                                        'phone': phone.value
                                    })).classes('w-full mt-2').props('color=primary')

                #cuando el boton se hace click aparece el formulario
                btn_interest.on('click', show_fields)

# --- RAIZ ---
@ui.page('/')
def client():
    global products, search_text

    #funcion para cargar los productos
    def load():
        global products
        products = get_products()
        render_grid.refresh()

    load()

    ui.colors(primary="#2E5077", secondary="#10b981", accent="#79D7BE")

    # Header / Navigation
    with ui.header().classes('bg-white text-slate-800 shadow-md p-4 justify-between items-center'):
        ui.label('PALLISER CATALOG').classes('text-xl font-black text-primary')

        #navegacion por pestañas
        with ui.tabs() as tabs:
            tab_catalog = ui.tab('CATÁLOGO', icon='grid_view')
            tab_cart = ui.tab('MI CARRITO', icon='shopping_cart')

    # Contenido de las pestañas, el catalogo es la vista principal
    with ui.tab_panels(tabs, value=tab_catalog).classes('w-full max-w-7xl mx-auto bg-transparent'):
        # PANEL CATÁLOGO
        with ui.tab_panel(tab_catalog):    #este bloque solo muestra la pestaña del catalogo
            with ui.row().classes('w-full items-center mb-6'):
                ui.input(placeholder="Buscar por nombre...",
                        on_change=lambda e: (globals().update(search_text=e.value), render_grid.refresh())) \
                    .classes('flex-grow').props('outlined rounded dense prepend-icon=search')

            render_grid()

        # PANEL CARRITO
        with ui.tab_panel(tab_cart):
            ui.label('MI SELECCIÓN').classes('text-2xl font-bold mb-6')
            render_cart()


if __name__ in {"__main__", "__mp_main__"}:
    ui.run(title="Catálogo | Client", port=8081, host="0.0.0.0")

    # 172.21.211.76:8081