import React from 'react';
import LinkedStateMixin from 'react-addons-linked-state-mixin';
import SkyLight from 'react-skylight';
import twoDecimalPlace from './view_account';
import {Bar, Line} from 'react-chartjs';
import {EditPurchase} from './importation_purchase';

export const API = '/import';

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
    "display_price",
    "box_code",
    "modify_strategy",
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
        console.log('items', this.props.items);
        var items = this.props.items.map(function(i, index) {
            return <option value={index}>{display(i)}</option>;
        });
        return (<select size={this.props.size} value={this.state.current} 
                        onChange={this.onchange} name={this.props.name}>
            {items}
        </select>);
    }
});



//
//            <div className="col-md-4">
//                <div className="myfloat">
//                </div>
//            </div>
//
export var ShowDeclared = React.createClass({
    setCurrent: function(current) {
        this.setState({current: current});
    },
    getAllProd: function() {
        $.ajax({
            url: API + '/declaredgood',
            success: (result) => {
                result = JSON.parse(result);
                this.setState({list: result.result});
            }
        }); 
    },
    getInitialState: function() {
        this.getAllProd();
        return {
            list: [],
            current: {},
        }
    },
    editProd: function(x) {
        this.setState({current: x}, function() {
            this.refs.editbox.fetchnew();
            this.refs.editProd.show();
        }.bind(this));
    },
    editedProd: function(newdeclared) {
        for (var i in this.state.list) {
            var x = this.state.list[i];
            if (x.uid == newdeclared.uid) {
                this.state.list[i] = newdeclared;
            }
        }
        this.setState({'list': this.state.list});
        this.refs.editProd.hide();
    },
    render: function() {
        return (<div className="container">
            <div className="row" >
            <SkyLight hiddenOnOverlayClicked ref="editProd" title="Editar Producto">
                <CreateOrUpdateBox url={API + "/declaredgood"} ref="editbox"
                     names={DECLARED_KEYS} update={true} uid={this.state.current.uid}
                     callback={this.editedProd} />
            </SkyLight>
            <div className="col-md-12">
            <table className="table" >
                {this.state.list.map((x) => {
                    return <tr>
                        <td><button onClick={this.editProd.bind(this, x)}>edit</button></td>
                        <td>{x.uid}</td>
                        <td>{x.display_name}</td>
                        <td>{x.display_price}</td>
                        <td>{x.box_code}</td>
                        <td>{x.modify_strategy}</td>
                    </tr>;
                })}
            </table>
            </div>
            </div>
        </div>);
    }
});

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
            url: API + '/universal_prod_with_declared',
            success: (result) => {
                result = JSON.parse(result);
                result.prod.sort((a,b) => {
                    if (a.unit > b.unit) {
                        return 1;
                    }
                    if (a.unit < b.unit) {
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
                <CreateOrUpdateBox url={API + "/universal_prod"} ref="editbox"
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
                <td>{prod.unit}</td>
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
            url: API + '/purchase',
            success: (x) => {
                x = JSON.parse(x);
                this.setState({list: x.result});
            }
        });
    },
    generateInv: function(item) {
        if (item.status == 'NEW') {
            alert('Aun no esta listo');
            return;
        }
        var proceed = true;
        if (item.status == 'CUSTOM') {
            proceed = confirm('Regenerar Factura borrara los combios hechos');
        }
        if (proceed) {
            $.ajax({
                url: API + '/custom_full/purchase/' + item.uid,
                method: 'POST',
                success: (x) => {
                    if (item.status != 'CUSTOM') {
                        item.status = 'CUSTOM';
                        this.setState({list: this.state.list});
                    }
                }
            });
        }
    },
    getInitialState: function() {
        this.getAllPurchase();
        return {list: []};
    },
    render: function() {
        return <div className="container">
            return <table className="table"><tbody>
                { this.state.list.map( (x) => {
                    return <tr>
                        <td>{x.uid}</td>
                        <td>{x.timestamp}</td>
                        <td>{x.status}</td>
                        <td><a href={API + "/purchase_detailed/" + x.uid + '.html'}>Ver Compras</a></td>
                        <td>{x.status == 'CUSTOM' ? 
                            <a className='btn btn-sm btn-primary' href={"#/edit_custom/" + x.uid}>
                                Editar Factura</a>:''}</td>
                        <td>{x.status != 'NEW' ? 
                            <button onClick={this.generateInv.bind(this, x)} 
                                className='btn btn-sm btn-warning'>
                               Generar Factura</button> : ''}</td>
                    </tr>;
                })}
        </tbody></table>
        </div>;
    }
});

export var ShowPurchase2 = React.createClass({
    getAllPurchase: function() {
        $.ajax({
            url: API + '/purchase',
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
    createPurchase: function() {
        $.ajax({
            url: API + '/purchase',
            method: 'POST',
            data: '{"status": "NEW"}',
            success: (result) => {
                var key = JSON.parse(result).key;
                window.location = '#/edit_purchase/' + key;
            }
        });
    },
    render: function() {
        return <div className="container">
            <button onClick={this.createPurchase}>{'创建新货柜'}</button>
            <PurchaseList2 list={this.state.list} />;
        </div>;
    }
});

var PurchaseList = React.createClass({
    render: function() {
    }
});

var PurchaseList2 = React.createClass({
    render: function() {
        return <table className="table"><tbody>
            { this.props.list.map( (x) => {
                return <tr>
                    <td>{x.uid}</td>
                    <td>{x.timestamp}</td>
                    <td>{x.status}</td>
                    <td><a href={API + "/purchase_detailed/" + x.uid + '.html?lang=zh'}>
                        {'查看'}</a></td>
                    <td><a className='btn btn-sm btn-primary' href={"#/edit_purchase/" + x.uid}>
                        {'编辑'}</a></td>
                </tr>;
            })}
        </tbody></table>;
    }
});

var InvMovementList = React.createClass({
    render: function() {
        return <table className="table">
            {this.props.items.map( (x) => {
                return <tr>
                    <td>{x.inventory_codename}</td>
                    <td>{x.inventory_docid}</td>
                    <td>{x.timestamp}</td>
                    <td>{x.status}</td>
                    <td>{x.origin}</td>
                    <td>{x.dest}</td>
                    <td>{x.trans_type}</td>
                    <td>{x.value_usd}</td>
                </tr>;
            })}
        </table>;
    }
});

export var InvMovementListFull = React.createClass({
    fetchData: function() {
        $.ajax({
            url: '/import/inv_movement/' + this.props.params.date,
            success: (result) => {
                result = JSON.parse(result);
                this.setState({'items': result.result});
            }
        });
    },
    getInitialState: function() {
        this.fetchData();
        return {'items': []};
    },
    render: function() {
        return <InvMovementList items={this.state.items} />
    }
});

var SaleReportByDate= React.createClass({
    render: function() {
        return <table className="table">
            <tr>
                <td>Fecha</td>
                <td>RUC</td>
                <td>Venta</td>
                <td>IVA</td>
                <td>Numeros de factura</td>
            </tr>;
            {this.props.items.map( (x) => {
                return <tr>
                    <td>{x.timestamp}</td>
                    <td>{x.ruc || ''}</td>
                    <td>{x.sale_pretax_usd}</td>
                    <td>{x.tax_usd}</td>
                    <td>{x.count}</td>
                    <td>{Number(x.sale_pretax_usd) / x.count}</td>
                </tr>;
            })}
        </table>;
    }
});

export var SaleReportByDateFull = React.createClass({
    fetchData: function(start, end) {
        $.ajax({
            url: `/import/sales_report?start=${start}&end=${end}`,
            success: (result) => {
                result = JSON.parse(result);
                console.log(result);
                this.setState({'items': result.result});
            }
        });
    },
    getInitialState: function() {
        console.log('getinitialstate');
        return {'items': []};
    },
    fetchDataClick() {
        var start = this.refs.start.value;
        var end = this.refs.end.value;
        console.log('here');
        this.fetchData(start, end);
    },
    render: function() {
        var labels = [];
        var thedata = [];
        var thedata2 = [];
        var values_by_date = {};
        var mayor_by_date = {};
        for (var x in this.state.items) {
            var y = this.state.items[x];
            if (!(y.timestamp in values_by_date)) {
                values_by_date[y.timestamp] = 0;
                mayor_by_date[y.timestamp] = 0;
            }
            if (y.ruc) {
                values_by_date[y.timestamp] += Number(y.sale_pretax_usd);
            } else {
                mayor_by_date[y.timestamp] += Number(y.sale_pretax_usd);
            }
        }
        labels = Object.keys(values_by_date);
        labels.sort();
        for (var x in labels) {
            var y = labels[x];
            thedata.push(values_by_date[y]);
            thedata2.push(mayor_by_date[y]);
        }

        var data = {
        labels: labels,
        datasets: [{
            fillColor: "blue",
            label: '零售',
            data: thedata,
            borderWidth: 1
        },{
            fillColor: "green",
            label: '批发',
            data: thedata2,
            borderWidth: 1
        }]
        };
        var options = {
        scales: {
            yAxes: [{
                ticks: {
                    beginAtZero:true
                }
            }]
        }
        };
        return <div className="container">
            Start: <input ref='start' />
            End: <input ref='end' />
            <button onClick={this.fetchDataClick} >Cargar</button>
            <SaleReportByDate items={this.state.items} />
            <Bar data={data} options={options} height="800" width="1000"/>
        </div>
    }
});
