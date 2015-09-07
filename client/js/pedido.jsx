React = require('react');

function display(x) {
    return x / 100;
}

var SearchBar = React.createClass({
    search: function() {
        alert('searching');
    },
    render: function() {
        return (<div>
        <button onClick={this.search}>Buscar</button>
        <input placeholder="codigo" ref="codigo" />
        </div>);

    }
});

var DisplayProduct = React.createClass({
    render: function() {
    }
});

var ItemTable = React.createClass({
    render: function() {
        var rows = this.props.items.map(function(x) {
            var precio = x.cant > x.prod.threshold ? x.prod.precio2 : x.prod.precio1;
            return (<tr>
                <td>{x.prod.codigo}</td>
                <td>{x.prod.nombre}</td>
                <td>{x.cant}</td>
                <td>{display(precio)}</td>
                <td>{display(precio * x.cant)}</td>
            </tr>);
        });
        return (<table>
            <tr>
                <th>Codigo</th>
                <th>Nombre</th>
                <th>Cantidad</th>
                <th>Precio</th>
                <th>Subtotal</th>
            </tr>
            {rows}
        </table>);
    }
});

/* Pedido's state:
   client = client info
   items = product items
   meta = total iva etc

   this.state is used for rendering only?
*/
var Pedido = React.createClass({
    setClient: function(client) {
        this.setState({'client': client});
    },
    addProd: function(prod, cant) {
        if (cant <= 0) {
            alert('cantidad menor a 0');
            return;
        }
        if (prod.codigo in this.allProd) {
            this.allProd[prod.codigo].cant += cant;
        } else {
            var index = this.state.items.length;
            this.allProd[prod.codigo] = {prod: prod, cant: cant, index: index};
        }
        this.setState({'items': this.exportprod(this.allProd)});
    },
    exportprod: function(items) {
        var result = [];
        for (var x in items) {
            var content = item[x];
            result[content.index] = content;
        }
        return result;
    },
    render: function() {
        return (
            <div>
            <ClientBox client={this.state.client}/>
            <ItemTable items={this.state.items}/>
            </div>
        );
    }
});
