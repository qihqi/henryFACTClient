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
    var newwindow=window.open("/static/buscar_producto.html",'name','height=700,width=500, scrollbars=yes');
    window.codigo_click = $(this).attr("id");
    if (window.focus) {
        newwindow.focus();
    }
    return false;
}
function getProdAjaxCall(codigo, callback) {
    var url = config.api + '/producto/' + codigo;
    getRequest(url, callback);
}

function searchProdAjax(prefix, callback) {
    var url = config.api + '/producto?prefijo=' + prefix;
    getRequest(url, callback);
}


var count=0;
function getRow() {
    var p = $("<tr>");
    var codigo_cell = $("<td>");
    var cant_cell = $("<td>");
    var nombre_cell = $("<td>");
    var buscar_cell = $("<td>");
    var trans_cell = $("<td>");
    var codigo = $("<input id=\"cod"+ count + "\" name=\"codigo\" class=\"text_field\">");
    var cant = $("<input id=\"cant"+ count + "\" name=\"cant\" class=\"text_field\">");
    var nombre = $("<span id=\"span"+ count + "\" name=\"nombre\" class=\"text_field\">");
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
    cant.addClass('cant');
    count++;
    p.beginning = codigo;
    return p;
}

function initEvents() {
    // make new row when enter is pressed on cantidad
    var isNumber = function (b) {
        return b!=undefined && b!=null && (b - 0) == b;
    };
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
            var cant = $('#cant' + id);
            var dest = $('#span' + id);
            var codigo = $(this).val();
            getProdAjaxCall(codigo, function(status, result) {
                if (status) {
                    dest.html(result.nombre);
                    cant.focus();
                } else {
                    dest.html("Codigo Equivocado");
                    $(this).select();
                }
            });
        }
    });
}

