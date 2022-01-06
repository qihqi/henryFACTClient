function getRequest(url, callback) {
    $.ajax({
        url: url,
        success: function(result) {
            var result = JSON.parse(result);
            callback(true, result);
        },
        failure: function(error, result) {
            callback(false, error);
        }
    });
}

function popup(){
    var newwindow=window.open("/static/buscar_prod.html",'name','height=700,width=500, scrollbars=yes');
    var bodegaId = getBodegaId();
    window.dest_id = $(this).attr('i');
    window.bodegaId = bodegaId;
    if (window.focus) {
        newwindow.focus();
    }
    return false;
}
function getProdAjaxCall(codigo, bodega_id, callback) {
    var url = '/app/api/item?prod_id=' + encodeURIComponent(codigo);
    getRequest(url, function(status, result) {
        if (status && result.result.length > 0) {
            var prod = {
                codigo: result.result[0].prod_id,
                nombre: result.result[0].name,
                unidad: result.result[0].unit
            };
            callback(true, prod);
        } else {
            callback(false, result);
        }
    });
}

function searchProdAjax(prefix, bodega_id, callback) {
    var url = '/app/api/item?name-prefix=' + prefix;
    getRequest(url, function(status, result) {
        if (status) {
            callback(status, result.result);
        }else {
            callback(status, result);
        }
    });
}

function getIngreso(codigo, callback) {
    var url = '/app/api/ingreso/' + codigo;
    getRequest(url, callback);
}


var count=0;
function getRow(includePrice) {
    var p = $("<tr>");
    var codigo_cell = $("<td>");
    var cant_cell = $("<td>");
    var nombre_cell = $("<td>");
    var buscar_cell = $("<td>");
    var trans_cell = $("<td>");
    var codigo = $("<input id=\"cod"+ count + "\" name=\"codigo\" class=\"text_field\">");
    codigo.attr('include_price', includePrice);
    var cant = $("<input id=\"cant"+ count + "\" name=\"cant\" class=\"text_field\">");
    var nombre = $("<span id=\"span"+ count + "\" name=\"nombre\" class=\"nombre\" class=\"text_field\">");
    var buscar = $("<a id=\"here"+ count + "\" name=\"nombre\" href=\"\" class=\"text_field\" >");
   // var trans = $("<input id=\"here"+ count + "\" name=\"transform\" class=\"text_field\" type=\"checkbox\">");
    buscar.click(popup);
    buscar.html("buscar");
    codigo_cell.append(codigo);
    cant_cell.append(cant);
    nombre_cell.append(nombre);
    buscar_cell.append(buscar);
    //trans_cell.append(trans);
    p.append(buscar_cell, codigo_cell, cant_cell, nombre_cell);
    codigo.addClass('codigo');
    codigo.attr('i', count);
    buscar.attr('i', count);
    nombre.attr('i', count);
    cant.addClass('cant');
    count++;
    p.beginning = codigo;
    if (includePrice) {
        var precio = $('<tr id=\"precio' + count + '\">');
        var subtotal = $('<tr id=\"subtotal' + count + '\">');
        p.append(precio);
        p.append(subtotal);
    }
    return p;
}

function displayMoney(s) {
    return s / 100;
}

function isNumber(b) {
    return b != undefined && b != null && (b - 0) == b;
};

function getBodegaId() {
    var type = $('#tipo').val();
    var bodegaId;
    if (type == 'INGRESO') {
        bodegaId = $('select[name="dest"]').val();
    } else {
        bodegaId = $('select[name="origin"]').val();
    }
    return bodegaId;
}

function initEvents() {
    $(document).on('keypress', '.cant', null, function (event) {
        if (event.which == 13) {
            event.preventDefault();
            var number = $(this).val();
            if (!isNumber(number)) {
                alert("cantidad debe ser numero");
                return;
            }
            var a = getRow();
            $("#insert").append(a);
            a.beginning.focus();
        }
    });


    $(document).on('keypress', '.codigo', null, function (event) {
        if (event.which == 13){
            event.preventDefault();
            var id = $(this).attr('i');
            var include_price = $(this).attr('include_price');
            var cant = $('#cant' + id);
            var dest = $('#span' + id);
            var codigo = $(this).val();
            var bodegaId = getBodegaId();
            getProdAjaxCall(codigo, bodegaId, function(status, result) {
                if (status) {
                    dest.html(result.nombre + ' (' + result.unidad + ')');
                    if (include_price) {
                        $('#price' + id).html(displayMoney(result.precio));
                    }
                    cant.focus();
                } else {
                    dest.html("Codigo Equivocado");
                    $(this).select();
                }
            });
        }
    });
}
