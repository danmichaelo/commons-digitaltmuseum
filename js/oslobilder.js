
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
            sortkey = val;
        switch (colname) {
        case 'institution':
            val = $.oslobilder.institutions[val];
            sortkey = val;
            break;
        case 'imageid':
            val = '<a class="external" href="http://www.oslobilder.no/' + row.institution + '/' + val + '">' + val + '</a>';
            sortkey = val;
            break;
        case 'sourcedate':
            sortkey = val.replace(/[^\d]/g, "");
            break;
        }
        if (val === sortkey) {
            return '<td>' + val + '</td>';
        } else {
            return '<td data-sort-value="' + sortkey + '">' + val + '</td>';
        }
    }

    function getData(addToHistory) {
        var postdata = $("form").serialize();
        if (addToHistory) {
            try {
                history.pushState(null, null, '?' + postdata);
            } catch (e) {
                // ignore old browser
            }
        }
        $.post("backend.fcgi", postdata, function (response) {
            var error = 0,
                nimgs = 0,
                i;
            try {
                response = $.parseJSON(response);
            } catch (e) {
                error = 1;
                // We report an error, and show the erronous JSON string (we replace all " by ', to prevent another error)
            }
            if (error === 1) {
                $('#errors').html(response);
                $('#results').html('');
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
                $('#results').html('<strong>Viser ' + nimgs + ' bilder:</strong>');
                $('#query').html('Spørringen var: ' + response.query);
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
        $.each($.oslobilder.institutions, function (key, value) {
            $('#inst_' + key).attr('checked', false);
        });

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
        if (nkeys > 0) {
            getData(false);
        } else {
            $.each($.oslobilder.institutions, function (key, value) {
                $('#inst_' + key).attr('checked', true);
            });
        }
    }


    $(document).ready(function () {

        $.each($.oslobilder.columns, function (index, value) {
            $('#chk_' + value).on('change', index, toggleColumns);
        });

        $('#alle_av').click(function (e) {
            $.each($.oslobilder.institutions, function (key, value) {
                $('#inst_' + key).attr('checked', false);
            });
            return false;
        });

        $('#alle_pa').click(function (e) {
            $.each($.oslobilder.institutions, function (key, value) {
                $('#inst_' + key).attr('checked', true);
            });
            return false;
        });

        $('.spinner')
            .hide()  // hide it initially
            .ajaxStart(function () {
                $(this).show();
                $(':submit').attr('disabled', true);
            })
            .ajaxStop(function () {
                $(this).hide();
                $(':submit').attr('disabled', false);
            });

        $('form').on('submit', function (e) {
            e.preventDefault();
            getData(true);
        });

        $(window).bind("popstate", function (e) {
            parseUrlParams();
        });
        parseUrlParams();

    });

}(jQuery));

