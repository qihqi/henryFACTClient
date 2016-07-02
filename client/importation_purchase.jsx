import React from 'react';
import ReactDOM from 'react-dom';
import LinkedStateMixin from 'react-addons-linked-state-mixin';
import SkyLight from 'react-skylight';
import twoDecimalPlace from './view_account';

const API = '/import';

// providor_name, upi's
//
function selectInput(ref) {
    var dom = ReactDOM.findDOMNode(ref);
    dom.focus();
    dom.select();
}
function testEnter(ref, event) {
    if (event.key == 'Enter') {
        selectInput(ref);
    }
}


function getItemValue(item) {
    return Math.round(item.price_rmb * item.quantity * 100) / 100;
}
/*
                <select ref='prod_select' onSelect={this.focusCant} >
                    {this.props.prods.map((x) => <option value={x.uid}>{x.name_zh}</option>)}
                </select>
                */


var EditItem = React.createClass({
    mixins: [LinkedStateMixin],
    getInitialState() {
        return { prod_detail: {name_zh: ''}, box: '', price_rmb: 0, quantity: 0};
    },
    saveEdited() {
        var providor_zh = this.state.prod_detail.providor_zh;
        var data = {
            box: this.state.box,
            price_rmb: this.state.price_rmb,
            quantity: this.state.quantity,
        };
        this.props.onEditedItem(this.state.itemPosition, data);
    },
    render() {
        return <table className="table"><tbody>
            <tr>
                <td>{"产品:"} </td>
                <td>{this.state.prod_detail.name_zh} ({this.state.prod_detail.unit})</td>
            </tr>
            <tr>
                <td>{"箱数:"} </td>
                <td><input valueLink={this.linkState('box')} /></td>
            </tr>
            <tr>
                <td>{"价格:"} </td>
                <td><input valueLink={this.linkState('price_rmb')} /></td>
            </tr>
            <tr>
                <td>{"数量:"} </td>
                <td><input valueLink={this.linkState('quantity')} /></td>
            </tr>
            <tr>
                <td>{"一共:"} </td>
                <td>{getItemValue(this.state)}</td>
            </tr>
            <tr>
                <td><button onClick={this.saveEdited}>{"确定"}</button> </td>
                <td></td>
            </tr>
            </tbody></table>;
    }
});

var NewProduct = React.createClass({
    mixins: [LinkedStateMixin],
    getInitialState() {
        return { };
    },
    saveNewProduct() {
        $.ajax({
            url: API + '/universal_prod',
            method: 'POST',
            data: JSON.stringify(this.state),
            success: (result) => {
                var key = JSON.parse(result).key;
                var newProd = Object.assign({}, this.state);
                newProd.uid = key;
                this.props.onNewProduct(newProd);
            }
        });
    },
    render() {
        return <table className="table"><tbody>
            <tr>
                <td>{"产品名:"} </td>
                <td><input valueLink={this.linkState('name_zh')} /></td>
            </tr>
            <tr>
                <td>Nombre Espanol:</td>
                <td><input valueLink={this.linkState('name_es')} /></td>
            </tr>
            <tr>
                <td>{"供货商:"} </td>
                <td><input valueLink={this.linkState('providor_zh')} /></td>
            </tr>
            <tr>
                <td>{"供货商产品号:"} </td>
                <td><input valueLink={this.linkState('providor_item_id')} /></td>
            </tr>
            <tr>
                <td>{"单位:"} </td>
                <td><input valueLink={this.linkState('unit')} /></td>
            </tr>
            <tr>
                <td>{"材料:"} </td>
                <td><input valueLink={this.linkState('material')} /></td>
            </tr>
            <tr>
                <td>{"卖货号:"} </td>
                <td><input valueLink={this.linkState('selling_id')} /></td>
            </tr>
            <tr>
                <td>{"说明:"} </td>
                <td><input valueLink={this.linkState('description')} /></td>
            </tr>
            <tr>
                <td></td>
                <td><button className="btn btn-lg btn-primary" 
                            onClick={this.saveNewProduct}>{"确定"}</button> </td>
            </tr>
            </tbody></table>;
    }
});

class ItemList extends React.Component {
    constructor(props) {
        super(props);
        this.onEditedItem = this.onEditedItem.bind(this);
    }
    onDeleteItem(item, event) {
        this.props.deleteItem(item, event.target.value);
    }
    editItem(item, itemPosition) {
        console.log(item); 
        var state = Object.assign({}, item.item);
        state['prod_detail'] = item.prod_detail;
        state['itemPosition'] = itemPosition;
        this.refs.createItemBox.setState(state);
        this.refs.createItem.show();
    }
    onEditedItem(itemPosition, data) {
        var item = this.props.items[itemPosition];
        this.props.onEditedItem(item, data);
        this.refs.createItem.hide();
    }
    render() {
        var rows = this.props.items.map((item, i) => {
            var moreStyle = ('_deleted' in item.item && item.item._deleted) ? {'text-decoration': 'line-through'} : {};
            if (('_new' in item.item && item.item._new) ||
                ('_edited' in item.item && item.item._edited)) {
                moreStyle['background-color'] = 'yellow';
            }
            return <tr style={moreStyle}>
                <td className="number">{item.item.box || ''}</td>
                <td>{item.prod_detail.name_zh}({item.prod_detail.unit})</td>
                <td className="number">{Number(item.item.price_rmb).toFixed(2)}</td>
                <td className="number">{Number(item.item.quantity)}</td>
                <td className="number">
                    {(Math.round(item.item.price_rmb*  item.item.quantity * 100) / 100).toFixed(2)}
                </td>
                <td><input type="checkbox"
                           checked={item.item._deleted}
                           onChange={this.onDeleteItem.bind(this, item)} /></td>
                <td><button type="button" onClick={this.editItem.bind(this, item, i)}>{'更改'}</button></td>
            </tr>;
       });
        return <div>
                <SkyLight hiddenOnOverlayClicked ref="createItem" title={"更改"}>
                    <EditItem ref="createItemBox" onEditedItem={this.onEditedItem} />
                </SkyLight>
                <table className="table">
                <thead>
                    <tr>
                        <th className="number">{"箱数"}</th>
                        <th>{"产品"}</th>
                        <th className="number">{"价格"}</th>
                        <th className="number">{"数量"}</th>
                        <th className="number">{"一共"}</th>
                        <th>{'删除？'}</th>
                        <th>{''}</th>
                    </tr>
                </thead>
                <tbody>
                    {rows}
                </tbody>
        </table>
        </div>;
    }
}

// props:
//  meta = Purchase
//  items = list of PurchaseItems
// state:
//  meta = Purchase,
//  items_by_providor = dict of providor -> list of items
//  providors = list of providors
export class EditPurchase extends React.Component {
    constructor(props) {
        super(props);
        this.setProvidorBox = this.setProvidorBox.bind(this);
        this.onNewItem = this.onNewItem.bind(this);
        this.onDeleteItem = this.onDeleteItem.bind(this);
        this.onEditedItem = this.onEditedItem.bind(this);
        this.onSelectProvidorVal = this.onSelectProvidorVal.bind(this);
        this.onNewProvidor = this.onNewProvidor.bind(this);
        this.savePurchase = this.savePurchase.bind(this);
        this.showAddNewProduct = this.showAddNewProduct.bind(this);
        this.onNewProduct = this.onNewProduct.bind(this);
        this.changeMeta = this.changeMeta.bind(this);
        this.getAllProducts();
        this.getFullInv(this.props.params.uid);
        this.state = {
            all_providors: [],
            providors: [],
            providors_data: {},
            allprod:{},
            items_by: {},
            currentProvidor: null,
            meta: {}
        };
    }
    onSelectProvidorVal(prov) {
        this.setState({currentProvidor: prov});
        this.refs.productSelector.focusPrice();
    }
    onNewProvidor(prov) {
        this.state.providors.push(prov);
        this.state.items_by[prov] = [];
        this.state.providors_data[prov] = {
            box: 0, total: 0};
        this.setState({
            providors: this.state.providors,
            items_by: this.state.items_by,
            providors_data: this.state.providors_data,
        });
    }
    getFullInv(uid) {
        $.ajax({
            url: API + '/purchase_full/' + uid,
            success: (result) => {
                if (typeof result === 'string') {
                    result = JSON.parse(result);
                }
                var providors = [];
                var items_by = {};
                var providors_data = {};
                for (var i in result.items) {
                    var item = result.items[i];
                    var prov = item.prod_detail.providor_zh;
                    if (!(prov in items_by)) {
                        items_by[prov] = [];
                        providors_data[prov] = {};
                        providors_data[prov].box = 0;
                        providors_data[prov].total = 0;
                        providors.push(prov);
                    }
                    items_by[prov].push(item);
                    providors_data[prov].box += Number(item.item.box) || 0;
                    providors_data[prov].total += getItemValue(item.item);
                }
                this.setState({
                    items_by: items_by,
                    providors: providors,
                    providors_data: providors_data,
                    meta: result.meta,
                });
            }
        });
    }
    getAllProducts() {
        $.ajax({
            url: API + '/universal_prod',
            success: (result) => {
                if (typeof result === 'string') {
                    result = JSON.parse(result);
                }
                var allprod = {};
                for (var x in result.result) {
                    var item = result.result[x];
                    if (!(item.providor_zh in allprod)) {
                        allprod[item.providor_zh] = [];
                    }
                    allprod[item.providor_zh].push(item);
                }
                var providors = Object.keys(allprod);
                this.setState({
                    all_providors: providors,
                    allprod: allprod,
                });
            }
        });
    }
    onNewItem(item) {
        this.state.items_by[item.prod_detail.providor_zh].push(item);
        this.state.providors_data[item.prod_detail.providor_zh].total += getItemValue(item.item);
        this.setState({items_by: this.state.items_by});
        var dom = ReactDOM.findDOMNode(this.refs.itemListContainer);
        dom.scrollTop = dom.scrollHeight + 50;
    }
    onDeleteItem(item, value) {
        if ('_deleted' in item.item) {
            item.item._deleted = !item.item._deleted;
        } else {
            item.item._deleted = true;
        }
        this.setState({items_by: this.state.items_by});
    }
    onEditedItem(item, content) {
        Object.assign(item.item, content);
        item.item._edited = true;
        this.setState({items_by: this.state.items_by});
    }
    setProvidorBox(event) {
        if (this.state.currentProvidor == null) {
            return;
        }
        var value = Number(event.target.value);
        this.state.providors_data[this.state.currentProvidor].box = value;
        this.setState({providors_data: this.state.providors_data});
    }
    savePurchase() {
        var payload = {
            meta: this.state.meta,
            create_items: [],
            delete_items: [],
            edit_items: [],
            providor_boxes: {},
        };

        for (var prov in this.state.items_by) {
            for (var j in this.state.items_by[prov]) {
                var item = this.state.items_by[prov][j];
                var deleted = '_deleted' in item.item && item.item._deleted;
                var isNew = '_new' in item.item && item.item._new;
                var edited = '_edited' in item.item && item.item._edited;
                if (isNew && deleted) {
                    // do nothing
                    continue;
                }
                if (deleted) {
                    // regardless of if edited 
                    payload.delete_items.push(item.item);
                    continue;
                }
                if (isNew) {
                    // regardless of edited
                    payload.create_items.push(item.item);
                    continue
                }
                if (edited) {
                    // not new and not deleted
                    payload.edit_items.push(item.item);
                }
            }
        }
        console.log(payload);
        $.ajax({
            url: API + '/purchase_full/' + this.props.params.uid,
            data: JSON.stringify(payload),
            method: 'PUT',
            success: (x) => {
                alert('保存成功');
                this.getFullInv(this.props.params.uid);
            }
        });
    }
    showAddNewProduct() {
        this.refs.addNewProductBox.setState({providor_zh: this.state.currentProvidor});
        this.refs.addNewProduct.show();
    }
    onNewProduct(product) {
        if (!(product.providor_zh in this.state.allprod)) {
            this.state.allprod[product.providor_zh] = [];
            this.state.all_providors.push(product.providor_zh);
        }
        this.state.allprod[product.providor_zh].push(product);
        this.setState({allprod: this.state.allprod, all_providors: this.state.all_providors});
        this.refs.addNewProduct.hide();
    }
    changeMeta(event) {
        this.state.meta[event.target.name] = event.target.value;
        this.setState({meta: this.state.meta});
    }
    render() {
        var currentItems = [];
        var currentAllProd = [];
        var currentData = {box: 0, total: 0};
        if (this.state.currentProvidor) {
            currentItems = this.state.items_by[this.state.currentProvidor];
            currentAllProd = this.state.allprod[this.state.currentProvidor];
            currentData = this.state.providors_data[this.state.currentProvidor];
        }
        const addNewProdStyle = {
            height: '70vh',
            marginTop: '-400px',
            overflowY: 'scroll',
        }

        return <div className="container" style={{height: '100%'}}>
            <SkyLight hiddenOnOverlayClicked dialogStyles={addNewProdStyle} ref="addNewProduct" title={"新产品"}>
                <NewProduct ref="addNewProductBox" onNewProduct={this.onNewProduct} />
            </SkyLight>
        <div className="row">
            <div className="col-sm-4">
                <p><label>{'货柜日期'}</label>
                <input name="timestamp" value={this.state.meta.timestamp} onChange={this.changeMeta}/></p>
                <label>{'上次更改'}</label>
                {this.state.meta.last_edit_timestamp}
            </div>
            <div className="col-sm-4">
                <p><label>{'订单毛重'}</label>
                <input name="total_gross_weight_kg" 
                       onChange={this.changeMeta} 
                       value={this.state.meta.total_gross_weight_kg}/></p>
                <label>{'订单箱数'}</label>
                <input name="total_box" onChange={this.changeMeta} value={this.state.meta.total_box} />
            </div>
            <div className="col-sm-4">
                <p><label>{'总价 '}</label>{this.state.meta.total_rmb}</p>
                <button onClick={this.showAddNewProduct}>{'添加新产品'}</button>
                <button onClick={this.savePurchase}>{'保存'}</button>
            </div>
        </div>
        <div className="row" style={{height: '90%'}}>
            <div className="col-sm-4" >
                <ProvidorSelector all_providors={this.state.all_providors}
                                  currentProvidor={this.state.currentProvidor}
                                  providors={this.state.providors}
                                  providors_data={this.state.providors_data}
                                  onNewProvidor={this.onNewProvidor}
                                  onSelectProvidor={this.onSelectProvidorVal}
                                  />
            </div>
            <div className="col-sm-8">
                <div className="row">
                    {this.state.currentProvidor}
                    <span style={{marginLeft: '200px'}}>{'箱数'}
                        <input ref='totalBox' value={currentData.box || ''}
                        onChange={this.setProvidorBox} /></span>
                    <span style={{marginLeft: '10px'}}>{'钱数'}
                        {currentData.total || ''}</span>
                </div>
                <div className="row">
                    <ProductSelector ref="productSelector" prods={currentAllProd}
                        onNewItem={this.onNewItem}/>
                </div>
                <div ref="itemListContainer" style={{height: '75vh',
                    'overflowY': 'scroll'}}>
                    <ItemList items={currentItems} deleteItem={this.onDeleteItem} 
                        onEditedItem={this.onEditedItem}/>
                </div>
            </div>
        </div>
        </div>;
    }
}
// all_providors
// providors
// providor_data
// onSelectProvidor
// onNewProvidor
class ProvidorSelector extends React.Component {
    constructor(props) {
        super(props);
        this.addProvidor = this.addProvidor.bind(this);
    }
    addProvidor(event) {
        var prov = this.refs.newProvidor.value;
        var index = this.props.providors.indexOf(prov);
        var dom = ReactDOM.findDOMNode(this.refs.allProvidorList);
        if (index != -1) {
            console.log(prov, 'exists');
            dom.scrollTop = 33 * index + 50;
        } else {
            this.props.onNewProvidor(prov);
            dom.scrollTop = dom.scrollHeight + 50;
        }
        this.props.onSelectProvidor(prov);
    }
    render() {
        return <div>
            <div>
                <select ref="newProvidor">
                    {this.props.all_providors.map((x) =>
                            <option key={x} value={x}>{x}</option>)}
                </select>
                <button onClick={this.addProvidor}>{'添加'}</button>
            </div>
            <div ref='allProvidorList' id="allProvidorList" style={{height: '75vh',
                'overflowY': 'scroll'}}>
             <table className="table"><tbody>
                 {this.props.providors.map((prov, pos) => {
                    return <tr className='selectable'
                        ref={'providorList' + pos}
                        value={prov}
                        onClick={this.props.onSelectProvidor.bind(null, prov)}>
                     <td><input type="radio" readOnly
                            name="selected_providor" value={prov}
                            checked={this.props.currentProvidor==prov}
                        />
                     </td>
                     <td>{prov}</td>
                     <td className="number">
                        {this.props.providors_data[prov].box}</td>
                     <td className="number">
                        {this.props.providors_data[prov].total.toFixed(2)}</td>
                     </tr>
                 })}
            </tbody></table>
            </div>
        </div>;
    }
}

class ProductSelector extends React.Component {
    constructor(props) {
        super(props);
        this.focusCant = this.focusCant.bind(this);
        this.focusPrice = this.focusPrice.bind(this);
        this.focusBox = this.focusBox.bind(this);
        this.addItem = this.addItem.bind(this);
        this.addItemOnKey = this.addItemOnKey.bind(this);
    }
    focusCant(event) {
        testEnter(this.refs.quantity, event);
    }
    focusBox(event) {
        testEnter(this.refs.box, event);
    }
    focusPrice(event) {
        console.log('here');
        selectInput(this.refs.price_rmb);
    }
    addItem(event) {
        if (!this.props.prods || this.props.prods.length == 0) {
            return;
        }
        var meta = {
            upi: this.refs.newProduct.value,
            quantity: this.refs.quantity.value,
            price_rmb: this.refs.price_rmb.value,
            box: this.refs.box.value,
            _new: true,
        };
        var prod_detail = null;
        for (var i in this.props.prods) {
            if (this.props.prods[i].upi == meta.upi) {
                prod_detail = this.props.prods[i];
            }
        }
        this.props.onNewItem({
            item: meta,
            prod_detail: prod_detail
        });
    }
    addItemOnKey(event) {
        if (event.key == 'Enter') {
            this.addItem()
        }
    }
    render() {
        return <div>
            <select ref="newProduct" onChange={this.focusPrice}>
            {this.props.prods.map((x) =>
                    <option key={x.upi} value={x.upi}>{x.name_zh}({x.unit})</option>)}
            </select>
            <input className="smallNum"
                ref="price_rmb" onKeyDown={this.focusCant} placeholder={'价格'}/>
            <input className="smallNum"
                ref="quantity" onKeyDown={this.focusBox} placeholder={'数量'}/>
            <input className="smallNum" onKeyDown={this.addItemOnKey}
                ref="box" placeholder={'箱数'}/>
            <button onClick={this.addItem}>{'添加'}</button>
        </div>;
    }
}
