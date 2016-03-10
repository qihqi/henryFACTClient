import React from 'react';
import LinkedStateMixin from 'react-addons-linked-state-mixin';
import ReactDOM from 'react-dom';


var ProdLoader = React.createClass({
    mixins: [LinkedStateMixin],
    getInitialState: function() {
        return {prod_id: null, cant: null, name: '', price: '', subtotal: ''};
    },
    handleCodigo: function(event) {
        if (event.key == 'Enter') {
            $.ajax({
                url: '/app/api/itemgroup?prod_id='+encodeURIComponent(this.refs.codigo.value),
                success: (x) => {
                    var result = JSON.parse(x).result;
                    if (result.length > 0) {
                        this.setState({name: result[0].name});
                        this.refs.cant.getDOMNode().focus();
                    }
                }
            });
        }
    },
    handleCant: function(event) {
        if (event.key == 'Enter') {
            console.log(this.state);
        }
    },
    render: function() {
        return <div className="row"> 
            <input placeholder="Codigo" ref='codigo' valueLink={this.linkState('prod_id')} onKeyPress={this.handleCodigo}/>
            <input placeholder="Cantidad" ref='cant' valueLink={this.linkState('cant')} onKeyPress={this.handleCant}/>
            {this.state.name}
            {this.state.price}
            {this.state.subtotal}
        </div>
    }
});

var ItemGroupCantList = React.createClass({
    render: function() {
        return <table className="table"><tbody>
            {this.props.items.map((c) => {
                return <tr>
                    <td>c.prod_id</td>
                    <td>c.cant</td>
                    <td>c.name</td>
                </tr>;
            })}
        </tbody></table>;

    };
});

var App = React.createClass({
    render: function() {
        return <div className="container">
            <div className="row">
                <ProdLoader callback={this.addItem} />
            </div>
            <div className="row">
            </div>
        </div>
    }
});

ReactDOM.render(<ProdLoader />, document.getElementById('content'));
