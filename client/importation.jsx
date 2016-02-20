import React from 'react';
import LinkedStateMixin from 'react-addons-linked-state-mixin';
import SkyLight from 'react-skylight';
import twoDecimalPlace from './view_account';

const PROD_KEYS = [
    "name_es",
    "name_zh",
    "providor_zh",
    "providor_item_id",
    "declaring_id",
    "selling_id",
    "unit"];

const DECLARED_KEYS = [
    "display_name", 
    "display_price" 
];

function query(url, callback) {
    $.ajax({
        url: url,
        success: callback
    });
}

function fetch_and_set_content(baseurl, callback) {
    return function(uid) {
        var url = baseurl + uid;
        query(url, callback);
    }
}

function setState(x) {
    this.setState(x);
}

// Ui form to create an object. 
// Creation triggered by POSTing to an url
// props: url <- where to post
//        names <- what are the names for the inputs
//        update <- used for update
//        uid <- if is update, the id of the element to be updated
//        callback <- call with updated version

var CreateOrUpdateBox = React.createClass({
    fetchnew: function() {
        $.ajax({
            url: this.props.url + '/' + this.props.uid,
            success: (x) => {
                x = JSON.parse(x);
                this.setState(x);
            },
        });
    },
    getInitialState: function() {
        var x = {};
        this.props.names.forEach(function(name) {
            x[name] = '';
        });
        var update = this.props.update || false;
        if (update) {
            query(this.props.url + '/' + this.props.uid,
                  setState.bind(this));
        }
        return x;
    }, 
    onchange: function(event) {
        var newstate = {};
        newstate[event.target.name] = event.target.value;
        this.setState(newstate);
    },
    submit: function(event) {
        event.preventDefault();
        var url = this.props.url;
        var method = 'POST';
        if (this.props.update) {
            method = 'PUT';
            url = this.props.url + '/' + this.props.uid;
        }
        this.props.callback(this.state);
        var end_result = {};
        for (var x in this.props.names) {
            var n = this.props.names[x];
            end_result[n] = this.state[n];
        }
        $.ajax({
            url: url,
            method: method,
            data: JSON.stringify(end_result),
            success: function(data) {
                this.setState({});
            }.bind(this)
        });
    },
    setDeclared: function(x) {
        var state = {};
        state[this.props.optionbox.name] = x.uid;
        this.setState(state);
    },
    render: function() {
        console.log(this.state);
        var inputs = this.props.names.map(function(name) {
            return <p> {name}: <input name={name} ref={name}
                value={this.state[name] || ''}
                onChange={this.onchange}/></p>;
        }.bind(this));
        if (this.props.optionbox) {
            inputs.push(<SelectBox name={this.props.optionbox.name} 
                        value={this.state[this.props.optionbox.name]}  
                        items={this.props.optionbox.items}
                        itemdisplay={this.props.optionbox.display}
                        size={this.props.optionbox.size}
                        callback={this.setDeclared}
                    /> );

        }
        var value = this.props.update ? 'update' : 'create';
        return (<form onSubmit={this.submit}>
            {inputs}
            <input type="submit" value={value}/>
        </form>);
    }
});

function render_input_for_keys(keys, classes) {
    return function() {
        var values = keys.map(function(name) {
            return (
                <p>
                {name}:
                <input name={name} ref={name}
                value={this.state[name]}
                onChange={this.handler.bind(this, name)}/>
                </p>
                );
        }.bind(this));
        return (<div class={classes}>
            {values}
            </div>);
    }
}



function display_list_of_item(names) {
    var list = {
        render: function() {
            var lists = this.props.list.map(function(i) {
                var innerhtml = '';
                for (var x in names) {
                    innerhtml += (' ' + i[names[x]]);
                }
                return <li> {innerhtml} </li>;
            });
            return (<ul>{lists}</ul>);
        }
    };
    return list;
}

// props input:
//   items: an array of items to be displayed
//   name: name of the select field
//   size: size of select field
//   callback: if an item is selected, callback is called with it.
//   itemdisplay: how ot display the item given in items.
var SelectBox = React.createClass({
    getInitialState: function() {
        return {'current': '0'};
    },
    onchange: function(event) {
        this.setState({current: event.target.value});
        var index = parseInt(event.target.value);
        if (this.props.callback != null) {
            this.props.callback(this.props.items[index]);
        }
    },
    render: function() {
        var display = this.props.itemdisplay;
        var items = this.props.items.map(function(i, index) {
            return <option value={index}>{display(i)}</option>;
        });
        return (<select size={this.props.size} value={this.state.current} 
                        onChange={this.onchange} name={this.props.name}>
            {items}
        </select>);
    }
});

var ProdCantPriceInput = React.createClass({
    getInitialState: function() {
        return {cant: 0, price: 0};
    },
    focus: function() {
        var cant = React.findDOMNode(this.refs.cant);
        cant.focus();
        cant.select();
    },
    onChangeCant: function(event) {
        this.setState({cant: event.target.value}); 
    },
    onChangePrice: function(event) {
        this.setState({price: event.target.value}); 
    },
    focusPrice: function(event) {
        if (event.nativeEvent.keyCode == 13) {
            event.preventDefault();
            var price = React.findDOMNode(this.refs.price);
            price.focus();
            price.select();
        }
    },
    exportItem: function(event) {
        if (event.nativeEvent.keyCode == 13) {
            event.preventDefault();
            this.props.callback({
                prod: this.props.prod,
                cant: this.state.cant,
                price: this.state.price
            });
        }
    },
    render: function() {
        var prod = this.props.prod || {};
        var prodname = prod.name_zh || (prod.providor_id + " " + prod.providor_item_id);
        var total = Math.round(this.state.cant * this.state.price * 100) / 100;
        return (
            <table>
            <tbody>
            <tr>
                <td>{prodname}</td>
                <td><input ref="cant" value={this.state.cant} onChange={this.onChangeCant} 
                           onKeyDown={this.focusPrice} /> </td>
                <td><input ref="price" value={this.state.price} 
                           onChange={this.onChangePrice} onKeyDown={this.exportItem}/></td>
                <td>{total}</td>
            </tr>
            </tbody>
            </table>
        );
    }
});

var ProductSearcher = React.createClass({
    getAllProduct: function(ready) {
        $.ajax({
            url: '/app/api/universal_prod', 
            success: (result) => {
                var result = JSON.parse(result);
                this.allprod = {};
                for (var x in result.result) {
                    var item = result.result[x];
                    if (!(item.providor_zh in this.allprod)) {
                        this.allprod[item.providor_zh] = [];
                    }
                    this.allprod[item.providor_zh].push(item);
                }
                console.log(this.allprod);
                var providors = Object.keys(this.allprod);
                this.setState({'providors': providors});    
            }
        });
    },
    getInitialState: function() {
        this.getAllProduct();
        return {providors: [], products: []};
    }, 
    onProvidorChange: function(prov) {
        var prods = this.allprod[prov] || [];
        console.log(this.allprod);
        this.setState({products: prods});
        if (prods.length > 0) {
            this.props.onSelectProduct(prods[0]);
        }
    },
    render: function() {
        return (<div className="container">
            <div className="row"><button onClick={this.getAllProduct}>Reload</button></div>
            <div className="row">
            <SelectBox items={this.state.providors}
                       size="10"
                       name="providor"
                       callback={this.onProvidorChange}
                       itemdisplay={function(x){return x;}}  />
            </div>
            <div className="row">
            <SelectBox items={this.state.products}
                       size="20"
                       name="product"
                       callback={this.props.onSelectProduct}
                       itemdisplay={displayProduct}  />
            </div>
           </div>);
    }
});

function displayProduct(p) {
    var chname = '(' + (p.providor_item_id || '') + ')' + p.name_zh;
    return chname + " " + p.name_es;
}

var ItemList = React.createClass({
    render: function() {
        var rows = this.props.items.map(function(item) {
            return <tr>
                <td>{displayProduct(item.prod)}</td>
                <td>{item.price}</td>
                <td>{item.cant}</td>
                <td>{Math.round(item.cant *  item.price * 100) / 100}</td>
            </tr>;
        });
        return <table>
            <thead>
                <tr>
                    <th>{"产品"}</th>
                    <th>{"价格"}</th>
                    <th>{"数量"}</th>
                    <th>{"一共"}</th>
                </tr>
            </thead>
            <tbody>
                {rows}
            </tbody>
        </table>
    }
});

export var CreateInvBox = React.createClass({
    getInitialState: function() {
        return {currentProd: {}, items: []};
    },
    onSelectProduct: function(prod) {
        console.log("onSelectProducto");
        console.log(prod);
        this.setState({currentProd: prod});
        this._input.focus();
    },
    addItem: function(item) {
        var arr = this.state.items.concat([item]);
        this.setState({items: arr});
    },
    saveInv: function() {
        $.ajax({
            method: 'POST',
            data: JSON.stringify(this.state.items),
            url: '/app/api/purchase_full',
            success: function(r) {
                alert(r.uid);
            }
        });
    },
    setInputRef: function(ref) {
        this._input = ref;
    },
    loadInv: function() {
        var code = React.findDOMNode(this.refs.code).value;
        query('/app/api/purchase_full/' + code, function(result) {
            this.setState({'items': result.result});
        }.bind(this));
    },
    render: function() {
        return <div className="container">
            <h4>{"购货"}</h4>
            <div className="row">
            <div className="col-xs-4 col-md-4">
                <ProductSearcher onSelectProduct={this.onSelectProduct} />
            </div>
            <div className="col-xs-8 col-md-8">
                <input ref="code" />
                <button onClick={this.loadInv}>LOAD</button>
                <button onClick={this.saveInv}>SAVE</button>
                <ProdCantPriceInput prod={this.state.currentProd} 
                                    ref={this.setInputRef} callback={this.addItem} />
                <ItemList items={this.state.items} />
            </div>
            </div>
        </div>;
    }
});
//
//            <div className="col-md-4">
//                <div className="myfloat">
//                </div>
//            </div>

export var ShowProd = React.createClass({
    setCurrent: function(current) {
        this.setState({current: current});
    },
    getDeclaredGood: function(uid) {
        if (uid in this.declared) {
            return this.declared[uid];
        }
        return {};
    },
    getAllProd: function() {
        $.ajax({
            url: '/app/api/universal_prod_with_declared',
            success: (result) => {
                result = JSON.parse(result);
                result.prod.sort((a,b) => {
                    if (a.providor_zh > b.providor_zh) {
                        return 1;
                    }
                    if (a.providor_zh < b.providor_zh) {
                        return -1;
                    }
                    return 0;
                });
                result.declared.sort((a,b) => {
                    if (a.display_name > b.display_name) {
                        return 1;
                    }
                    if (a.display_name < b.display_name) {
                        return -1;
                    }
                    return 0;
                });
                this.setState({list: result.prod, declaredgoods: result.declared});
            }
        }); 
    },
    getInitialState: function() {
        this.getAllProd();
        return {
            current: 1,
            list: [],
            declaredgoods: []
        }
    },
    editProd: function(x) {
        this.setState({current: x}, function() {
            this.refs.editbox.fetchnew();
            this.refs.editProd.show();
        }.bind(this));
    },
    editedProd: function(newprod) {
        var newlist = this.state.list.slice();
        for (var i in this.state.declaredgoods) {
            if (newprod.declaring_id == this.state.declaredgoods[i].uid) {
                newprod.declared_name = this.state.declaredgoods[i].display_name;
            }
        }
        for (var i in newlist) {
            if (newlist[i].upi == newprod.upi) {
                newlist[i] = newprod;
            }
        }
        this.setState({'list': newlist});
        this.refs.editProd.hide();
    },
    displayDeclared: function(x) {
        return x.display_name;
    },
    setDeclared: function(x) {
        this.declared = x.uid;
    },
    render: function() {
        var optionbox = {
            name: 'declaring_id', 
            items: this.state.declaredgoods, 
            display: this.displayDeclared,
            size: 1
        };
        return (<div className="container">
            <div className="row" >
            <SkyLight hiddenOnOverlayClicked ref="editProd" title="Editar Producto">
                <CreateOrUpdateBox url="/app/api/universal_prod" ref="editbox"
                     names={PROD_KEYS} update={true} uid={this.state.current}
                     optionbox={optionbox}
                     callback={this.editedProd} />
            </SkyLight>
            <div className="col-md-12">
                <ProdList list={this.state.list} click={this.editProd} declaredgoods={this.state.declaredgoods}/>
            </div>
            </div>
        </div>);
    }
});

var ProdList = React.createClass({
    render: function() {
        var click = this.props.click;
        var getDeclared = this.props.getDeclared;
        var makerow = function(prod) {
            var clickhandler = function() {
                console.log('click logger');
                console.log(prod);
                click(prod.upi);
            };
            return (<tr key={prod.uid}>
                <td><button onClick={clickhandler}>edit</button></td>
                <td>{prod.name_es}</td>
                <td>{prod.name_zh}</td>
                <td>{prod.providor_zh}</td>
                <td>{prod.providor_item_id}</td>
                <td>{prod.declared_name}</td>
                <td>{prod.selling_id}</td>
            </tr>);
        }

        var rows = this.props.list.map(makerow);
        return (
            <div> 
            <table className="table">
            <tr>
                <th>#</th>
                <th>{"西语"}</th>
                <th>{"中文"}</th>
                <th>{"供货商"}</th>
                <th>{"供货商号"}</th>
                <th>{"报关名称"}</th>
                <th>{"卖货号"}</th>
            </tr>
            <tbody>
            {rows}
            </tbody>
            </table>
            </div>);
    }
});

export var ShowPurchase = React.createClass({
    getAllPurchase: function() {
        $.ajax({
            url: '/app/api/purchase',
            success: (x) => {
                x = JSON.parse(x);
                this.setState({list: x.result});
            }
        });
    },
    getInitialState: function() {
        this.getAllPurchase();
        return {list: []};
    },
    render: function() {
        console.log('here');
        return <PurchaseList list={this.state.list} />;
    }
});

export var PurchaseContent = React.createClass({
    getItems: function() {
        $.ajax({
            url: '/app/api/purchase_full/' + this.props.params.uid,
            success: (x) => {
                x = JSON.parse(x);
                this.setState(x);
            }
        });
    },
    getInitialState: function() {
        this.getItems();
        return {items: [], meta: {timestamp: ''}};
    },
    render: function() {
        var total = 0;
        for (var i in this.state.items) {
            var x = this.state.items[i];
            x.item.quantity = Number(x.item.quantity);
            x.item.price_rmb = Number(x.item.price_rmb);
            total += x.item.quantity * x.item.price_rmb;
        }
        return <div className="col-md-12">
            {total}
            {this.state.meta.timestamp}
         <PurchaseItemList list={this.state.items} />;
        </div>
    } 
});

var PurchaseItemList = React.createClass({
    render: function() {
        return <table className="table"><tbody>
            <tr>
                <td>x.item.uid</td>
                <td>x.prod_detail.name_zh</td>
                <td>x.item.color</td>
                <td>x.item.quantity</td>
                <td>x.item.price_rmb</td>
                <td>total</td>
            </tr>
            { this.props.list.map( (x) => {
                return <tr>
                    <td>{x.item.uid}</td>
                    <td>{x.prod_detail.name_zh}</td>
                    <td>{x.prod_detail.selling_id}</td>
                    <td>{x.item.quantity}</td>
                    <td>{Math.round(x.item.price_rmb * 1000) / 1000  }</td>
                    <td>{Math.round(x.item.price_rmb * x.item.quantity * 1000) / 100}</td>
                </tr>;
            })}
        </tbody></table>;
    }
});

var PurchaseList = React.createClass({
    render: function() {
        return <table className="table"><tbody>
            { this.props.list.map( (x) => {
                return <tr>
                    <td><a href={"#/purchase/" + x.uid}>{x.uid}</a></td>
                    <td>{x.providor}</td>
                    <td>{x.total_rmb}</td>
                    <td>{x.timestamp}</td>
                </tr>;
            })}
        </tbody></table>;
    }
});
