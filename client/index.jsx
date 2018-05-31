import {ProdApp} from './CreateProduct';
import {ViewSingleItem} from './view_product';
import {SearchItemgroup} from './product';
import ReactDOM from 'react-dom';
import React from 'react';
import {Route, Router, Link, hashHistory} from 'react-router'

var router = <Router history={hashHistory}>
    <Route name="viewprod" path='/view_prod' component={SearchItemgroup} />
    <Route name="viewprod2" path='/view_prod/:search_term' component={SearchItemgroup} />
    <Route name="viewitem" path='/ig/:itemgroupid' component={ViewSingleItem} />
    <Route name="createprod" path='/' component={ProdApp} />
</Router>;
ReactDOM.render(router, document.getElementById('content'));

