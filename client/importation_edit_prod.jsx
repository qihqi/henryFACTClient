import React from 'react';
import ReactDOM from 'react-dom';
import LinkedStateMixin from 'react-addons-linked-state-mixin';
import SkyLight from './skylight';
import twoDecimalPlace from './view_account';
import {API} from './importation';

// To create a product
export var NewProduct = React.createClass({
    mixins: [LinkedStateMixin],
    getInitialState() {
        return { };
    },
    saveNewProduct() {
        var edit = 'edit' in this.props;
        var method = 'POST';
        var url = API + '/universal_prod';
        if (edit) {
            url = url + '/' + this.state.upi;
            method = 'PUT';
        }
        $.ajax({
            url: url,
            method: method,
            data: JSON.stringify(this.state),
            success: (result) => {
                var newProd = Object.assign({}, this.state);
                if (!edit) {
                    var key = JSON.parse(result).key;
                    newProd.upi = key;
                    this.props.onNewProduct(newProd);
                } else {
                    this.props.onNewProduct(newProd, this.index);
                }
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
                <td><select valueLink={this.linkState('unit')}>
                        {Object.keys(this.props.units).map((x) => <option value={x}>{this.props.units[x].name_zh}</option>)}
                    </select>
                </td>
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
                <td>{"报关条目:"} </td>
                <td><select valueLink={this.linkState('declaring_id')}>
                        {this.props.declared.map(
                                (x) => <option value={x.uid}>{x.display_name}</option>)}
                    </select>
                </td>
            </tr>
            <tr>
                <td></td>
                <td><button className="btn btn-lg btn-primary" 
                            onClick={this.saveNewProduct}>{"确定"}</button> </td>
            </tr>
            </tbody></table>;
    }
});

export var NewDeclared = React.createClass({
    mixins: [LinkedStateMixin],
    getInitialState() {
        return { };
    },
    saveNewItem() {
        var url = API + '/declaredgood';
        var method = 'POST';
        var edit = 'edit' in this.props
        if (edit) {
            url = url + '/' + this.state.uid;
            method = 'PUT';
        }
        $.ajax({
            url: url,
            method: method,
            data: JSON.stringify(this.state),
            success: (result) => {
                var newDeclared = Object.assign({}, this.state);
                if (!edit) {
                    var key = JSON.parse(result).key;
                    newDeclared.uid = key;
                    this.props.onNewItem(newDeclared);
                } else {
                    this.props.onNewItem(newDeclared, this.index);
                }
            }
        });
    },
    render() {
        return <table className="table"><tbody>
            <tr>
                <td>{"Display Name"} </td>
                <td><input valueLink={this.linkState('display_name')} /></td>
            </tr>
            <tr>
                <td>{"Display Price"} </td>
                <td><input valueLink={this.linkState('display_price')} /></td>
            </tr>
            <tr>
                <td>{"Box Code"} </td>
                <td><input valueLink={this.linkState('box_code')} /></td>
            </tr>
            <tr>
                <td>{"Modify Strategy"} (docena, convert_to_kg) </td>
                <td><select valueLink={this.linkState('modify_strategy')}>
                        <option value="">none</option>
                        <option value="docena">docena</option>
                        <option value="convert_to_kg">convert_to_kg</option>
                    </select>
                </td>
            </tr>
            <tr>
                <td></td>
                <td><button className="btn btn-lg btn-primary" 
                            onClick={this.saveNewItem}>{"确定"}</button> </td>
            </tr>
            </tbody></table>;
    }
});

const FIX_HEADER = {position: 'fixed', top: '0', width:'100%', zIndex: 10, backgroundColor: 'white'};
const DIALOG_STYLE = {
    height: '70vh',
    marginTop: '-200px',
    overflowY: 'scroll',
}

export class EditProdPage extends React.Component {
    constructor(props) {
        super(props);
        this.state = {prod:[], declaredgoods: [], units:{}};
        this.onNewProduct = this.onNewProduct.bind(this);
        this.onNewDeclared = this.onNewDeclared.bind(this);
        this.onEditedProduct = this.onEditedProduct.bind(this); 
        this.editProduct = this.editProduct.bind(this); 
        this.editDeclared = this.editDeclared.bind(this); 
        this.onEditedDeclared = this.onEditedDeclared.bind(this); 
        this.getAllProd();
        this.getAllUnits();
    }
    getAllUnits() {
        $.ajax({
            url: API + '/unit',
            success: (x) => {
                x = JSON.parse(x);
                this.setState({units: x});
            }
        });

    }
    getAllProd() {
        $.ajax({
            url: API + '/universal_prod_with_declared',
            success: (result) => {
                result = JSON.parse(result);
                result.prod.sort((a, b) => a.providor_zh.localeCompare(b.providor_zh, [ "zh-CN-u-co-pinyin" ]));
                result.declared.sort((a,b) => {
                    if (a.display_name > b.display_name) {
                        return 1;
                    }
                    if (a.display_name < b.display_name) {
                        return -1;
                    }
                    return 0;
                });
                this.setState({prod: result.prod, declaredgoods: result.declared});
            }
        }); 
    }
    onNewProduct(prod) {
        this.state.prod.push(prod);
        this.setState({prod: this.state.prod});
        this.refs.createProduct.hide();
    }
    onNewDeclared(declared) {
        this.state.declaredgoods.push(declared);
        this.setState({declaredgoods: this.state.declaredgoods});
        this.refs.createDeclared.hide();
    }
    onEditedProduct(prod, index) {
        Object.assign(this.state.prod[index], prod);
        this.setState({prod: this.state.prod});
        this.refs.editProductDialog.hide();
    }
    editProduct(prod, index) {
        this.refs.editProductDialog.show();
        this.refs.editProduct.setState(prod);
        this.refs.editProduct.index = index;
    }
    onEditedDeclared(declared, index) {
        Object.assign(this.state.declaredgoods[index], declared);
        this.setState({declaredgoods: this.state.declaredgoods});
        this.refs.editDeclaredDialog.hide();
    }
    editDeclared(declared, index) {
        this.refs.editDeclaredDialog.show();
        this.refs.editDeclared.setState(declared);
        this.refs.editDeclared.index = index;
    }
    render() {
        return <div className="container">
            <SkyLight dialogStyles={DIALOG_STYLE} 
                    hiddenOnOverlayClicked ref="createProduct" title={"Product"}>
                <NewProduct ref="addNewProductBox" 
                    units={this.state.units} 
                    onNewProduct={this.onNewProduct} 
                    declared={this.state.declaredgoods} />
            </SkyLight>
            <SkyLight hiddenOnOverlayClicked ref="createDeclared" title={"Declared"}>
                <NewDeclared ref="addNewProductBox" 
                    onNewItem={this.onNewDeclared} 
                     />
            </SkyLight>
            <SkyLight dialogStyles={DIALOG_STYLE} 
                    hiddenOnOverlayClicked ref="editProductDialog" title={"Edit Product"}>
                <NewProduct ref="editProduct" 
                    edit
                    units={this.state.units} 
                    onNewProduct={this.onEditedProduct} 
                    declared={this.state.declaredgoods} />
            </SkyLight>
            <SkyLight hiddenOnOverlayClicked ref="editDeclaredDialog" title={"Edit Declared"}>
                <NewDeclared ref="editDeclared"  edit
                    onNewItem={this.onEditedDeclared} />
            </SkyLight>
            <div style={FIX_HEADER}>
                <button onClick={()=>this.refs.createProduct.show()}>New Product</button>
                <button onClick={()=>this.refs.createDeclared.show()}>New Declared</button>
            </div>
            <div className="row">
                <h3>Declared Goods:</h3>
                <div className="col-sm-12">
                    <DeclaredList list={this.state.declaredgoods}  
                                  onItemSelected={this.editDeclared}/>
                </div>
            </div>
            <div className="row">
                <h3>Products:</h3>
                <div className="col-sm-12">
                    <ProductList list={this.state.prod} onItemSelected={this.editProduct} />
                </div>
            </div>
        </div>;
    }
}

var ProductList = React.createClass({
    render: function() {
        var click = this.props.click;
        var getDeclared = this.props.getDeclared;
        var makerow = (prod, index) => {
            return (<tr key={prod.uid}>
                <td><button onClick={this.props.onItemSelected.bind(null, prod, index)}>
                    edit</button></td>
                <td>{prod.name_es}</td>
                <td>{prod.name_zh}</td>
                <td>{prod.unit}</td>
                <td>{prod.providor_zh}</td>
                <td>{prod.providor_item_id}</td>
                <td>{prod.declaring_id}</td>
                <td>{prod.selling_id}</td>
            </tr>);
        }

        return (
            <table className="table">
            <tbody>
            {this.props.list.map(makerow)}
            </tbody>
            </table>
            );
    }
});

class DeclaredList extends React.Component {
    constructor(props) {
        super(props);
    }
    render() {
        return <table className="table" >
            {this.props.list.map((x, index) => {
                return <tr>
                    <td><button onClick={this.props.onItemSelected.bind(null, x, index)}>edit</button></td>
                    <td>{x.uid}</td>
                    <td>{x.display_name}</td>
                    <td>{x.display_price}</td>
                    <td>{x.box_code}</td>
                    <td>{x.modify_strategy}</td>
                </tr>;
            })}
        </table>;
    }
}
