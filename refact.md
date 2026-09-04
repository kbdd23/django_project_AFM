from arbitrary import creation.interpretation //fake module in order to justify the method ideas
from index.html import *

class DeattachTemplates(index.html):
    
    def abstract_templates(): 
        template_base = init_base_template()
        template_1 = inicio.as_concept()
        template_2 = menu.as_concept()
        template_3 = reservas.as_concept()

    def abstract_js(js_code):
        
        for rules in js_code:
            put_in_file(dir="static/js/")

class CreateTemplate()
    def create():
        create_template("admin-dashboard.html")
        


//El objetivo es crear un template base para que los diferentes templates abstraidos del monolito index.html hereden estilos y reglas js.
//Y separar las reglas de js embebidas en este en un archivo único. 

