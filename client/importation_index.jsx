import ReactDOM from 'react-dom';
import React from 'react';
import {Route, Router, Link, browserHistory} from 'react-router';
import {CreateInvBox, ShowProd, ShowPurchase, PurchaseContent} from './importation';

var ShowIndex = React.createClass({
    render: function() {
        return <ul>
            <li><a href="#/createpurchase">Crear Importacion {"创建新进口"}</a></li>
            <li><a href="#/allprod">Productos {"产品"}</a></li>
            <li><a href="#/allpurchase">Importaciones pasados {"进口"}</a></li>
        </ul>;
    }
});

var router = <Router history={browserHistory}>
    <Route name="createpurchase" path='/createpurchase' component={CreateInvBox} />
    <Route name="allprod" path='/allprod' component={ShowProd} />
    <Route name="allpurchase" path='/allpurchase' component={ShowPurchase} />
    <Route name="purchase" path='/purchase/:uid' component={PurchaseContent} />
    <Route name="index" path='/' component={ShowIndex} />
</Router>;
ReactDOM.render(router, document.getElementById("content"));

