
(function ($) {
    "use strict";

    function toggleColumns() {
        var i, j;
        for (i = 0; i < $.oslobilder.columns.length; i++) {
            j = i + 1;
            if ($('#chk_' + $.oslobilder.columns[i]).attr('checked') === 'checked') {
                $('table#oslobilder th:nth-child(' + j + '), table#oslobilder td:nth-child(' + j + ')').show();
            } else {
                $('table#oslobilder th:nth-child(' + j + '), table#oslobilder td:nth-child(' + j + ')').hide();
            }
        }
    }

    function formatCol(row, colno) {
        var colname = $.oslobilder.columns[colno],
            val = row[colname],
            sortkey = val,
            d;
        switch (colname) {
        case 'institution':
            val = $.oslobilder.institutions[val];
            sortkey = val;
            break;
        case 'imageid':
            val = '<a class="external" href="http://www.oslobilder.no/' + row.institution + '/' + val + '">' + val + '</a>';
            sortkey = val;
            break;
        case 'date':
            sortkey = val.replace(/[^\d]/g, "");
            for (var i = 8-sortkey.length; i > 0; i--) {
                sortkey += '0';
            }
            break;
        case 'upload_date':
            d = new Date(val*1000);
            val = d.toString("d. MMM yyyy");
            break;
        }
        if (val === sortkey) {
            return '<td class="' + colname + '">' + val + '</td>';
        } else {
            return '<td class="' + colname + '" data-sort-value="' + sortkey + '">' + val + '</td>';
        }
    }

    function prepareData(addToHistory) {
        var postdata = $('form tr:not(#institutions) input[value!=""]'),
            url;
        if ($('form tr#institutions :checked').length != $('form tr#institutions :checkbox').length) {
            postdata = postdata.add('form tr#institutions :checked');
        }
        if (parseInt($('form #limit').val()) != $.oslobilder.default_limit) {
            postdata = postdata.add('form #limit');
        }
        if ($('form #sort').val() != $.oslobilder.default_sort) {
            postdata = postdata.add('form #sort');
        }
        if ($('form #sortorder').val() != $.oslobilder.default_sortorder) {
            postdata = postdata.add('form #sortorder');
        }
        postdata = postdata.serialize();
        if (addToHistory) {
            try {
                url = './'
                if (postdata.length > 0) {
                    url += '?' + postdata;
                }
                history.pushState(null, null, url)
            } catch (e) {
                //alert(e.message)
                // ignore old browser
            }
        }
        return postdata;
    }

    function getData(addToHistory) {
        var postdata = prepareData(addToHistory);
        $.post("backend.fcgi", postdata, function (response) {
            var error = 0,
                nimgs = 0,
                i;
            //console.log("OK");
            //console.log(response);
            //try {
            //    response = $.parseJSON(response);
            //} catch (e) {
            //    error = 1;
            //    // We report an error, and show the erronous JSON string (we replace all " by ', to prevent another error)
            //}
            if (error === 1) {
                $('#errors').html(response);
                $('#results-intro').html('');
                $('#errors').show();
            } else {
                $('#errors').hide();
                $('table#oslobilder > tbody').html('');
                $.each(response.rows, function (index, row) {
                    var rowhtml = '<tr>', d = '', col = '', inst = '', imgid = '';
                    nimgs += 1;
                    for (i = 0; i < $.oslobilder.columns.length; i++) {
                        rowhtml += formatCol(row, i);
                    }
                    $('table#oslobilder > tbody').append(rowhtml);
                });
                var sortOrder = [$('form #sort')[0].selectedIndex];
                if ($('form #sortorder').val() == 'asc') {
                    sortOrder.push(0);
                } else {
                    sortOrder.push(1);
                }
                $('table#oslobilder').trigger('sorton', [sortOrder]);
                $('#results-intro').html('<strong>Viser ' + nimgs + ' bilder:</strong>');
                $('#query').html('Spørringen var: ' + response.query + '<br />Sidegenereringstid: ' + response.time + ' ms');
                $('#results').fadeIn("slow");
                toggleColumns();
            }
        });
    }

    function parseUrlParams() {
        var match,
            pl     = /\+/g,  // Regex for replacing addition symbol with a space
            search = /([\w]+)=?([^&]*)/g,
            decode = function (s) { return decodeURIComponent(s.replace(pl, " ")); },
            query  = window.location.search.substring(1),
            key = "",
            val = "",
            nkeys = 0;

        $('#collection').val('');
        $('#author').val('');
        $('#institutions :checkbox').attr('checked', false);

        while ((match = search.exec(query)) !== null) {
            nkeys += 1;
            key = decode(match[1]);
            val = decode(match[2]);
            if (val === 'on') {
                $('#' + key).attr('checked', true);
            } else {
                $('#' + key).val(val);
            }
        }
        if ($('#institutions :checked').length == 0) {
            $('#institutions :checkbox').attr('checked', true);
        }

        if (nkeys > 0) {
            getData(false);
        }
    }

    function resetForm(e) {

        $('#institutions :checkbox').attr('checked', true);
        $(':text').val('');
        $('#limit').val($.oslobilder.default_limit);
        $('#sort').val($.oslobilder.default_sort);
        $('#sortorder').val($.oslobilder.default_sortorder);
        prepareData(true);

    }


    $(document).ready(function () {

        $.each($.oslobilder.columns, function (index, value) {
            $('#chk_' + value).on('change', index, toggleColumns);
        });

        $('#alle_av').click(function (e) {
            $('#institutions :checkbox').attr('checked', false);
            return false;
        });

        $('#alle_pa').click(function (e) {
            $('#institutions :checkbox').attr('checked', true);
            return false;
        });

        $('.spinner')
            .hide()  // hide it initially
            .ajaxStart(function () {
                $(this).show();
                $(':button,:submit').attr('disabled', true);
            })
            .ajaxStop(function () {
                $(this).hide();
                $(':button,:submit').attr('disabled', false);
            });

        $('form').on('submit', function (e) {
            e.preventDefault();
            getData(true);
        });
        $('form button[type!=submit]').on('click', resetForm);

        $(window).bind("popstate", function (e) {
            parseUrlParams();
        });
        parseUrlParams();

    });

}(jQuery));

