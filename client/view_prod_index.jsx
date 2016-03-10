import {ViewSingleItem} from './view_product';
import {SearchItemgroup} from './product';
import ReactDOM from 'react-dom';
import React from 'react';

import {Route, Router, Link, browserHistory} from 'react-router'

var router = <Router history={browserHistory}>
    <Route path='/ig/:itemgroupid' component={ViewSingleItem} />
    <Route path='/' component={SearchItemgroup} />
</Router>

ReactDOM.render(router, document.getElementById('content'));
