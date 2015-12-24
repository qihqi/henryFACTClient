from .web import webmain
from .web_inventory import web_inventory_webapp
from .web_invoice import webinvoice
from .web_prod import webprod
from .accounting import accounting_webapp
from .advanced import webadv
from .web_internal_acct import internal_acct

webmain.merge(web_inventory_webapp)
webmain.merge(webinvoice)
webmain.merge(webprod)
webmain.merge(accounting_webapp)
# webmain.merge(internal_acct)
webmain.merge(webadv)
