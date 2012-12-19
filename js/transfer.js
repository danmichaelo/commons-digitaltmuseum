
function getQueryVariable(variable, query) {
    // http://stackoverflow.com/questions/2090551/parse-query-string-in-javascript
    if (query === undefined) {
        query = window.location.search.substring(1);
    }
    var vars = query.split('&');
    for (var i = 0; i < vars.length; i++) {
        var pair = vars[i].split('=');
        if (decodeURIComponent(pair[0]) == variable) {
            return decodeURIComponent(pair[1]);
        }
    }
    console.log('Query variable %s not found', variable);
}

function kortform(s) {
    switch (s.toLowerCase()) {
        case 'oslo museum':
            return 'OMU';
        case 'oslo byarkiv':
            return 'BAR';
        case 'norsk folkemuseum':
            return 'NF';
        case 'arbeiderbevegelsens arkiv og bibliotek':
            return 'ARB';
        case 'telemuseet':
            return 'TELE';
        case 'teknisk museum':
            return 'NTM';
        case 'universitetsbiblioteket i bergen':
            return 'UBB';
        case 'dextra photo':
            return 'KFS';
        default:
            return 'UNKNOWN';
    }

}

$(document).ready(function(){

    var license, author, dato, year, institusjon, inst, bildenr, samling, historikk, motiv, tittel, src;

    $('div#info').hide();
    $('form#upload').hide();

    $('.spinner')
        .hide()  // hide it initially
        .ajaxStart(function () {
            $(this).show();
            $(':button,:submit').attr('disabled', true);
            $('div#info').hide();
            $('form#upload').hide();
        })
        .ajaxStop(function () {
            $(this).hide();
            $(':button,:submit').attr('disabled', false);
        });

    function fill_desc() {
        var imgFilename = '',
            beskrivelse = '',
            desc = '';
        if (motiv != "NOTFOUND") {
            beskrivelse += motiv + '.';
        } else if (tittel != "NOTFOUND") {
            beskrivelse += tittel + '.';
        }
        if (historikk != "NOTFOUND") {
            beskrivelse += ' ' + historikk + '.';
        }
        var lics = $('select.license');
        if (lics.length > 0) {
            license = "";
            $.each(lics, function(ind, lic) {
                license += $(lic).val() + "\n";
            });
        } else {
            license = '{{' + license + '}}';
        }
        desc = ['',
            '=={{int:filedesc}}==',
            '{{Information',
            '|description = {{no|1=' + beskrivelse + '}}',
            '|source = {{Oslobilder|' + inst + '|' + bildenr + '|collection=' + samling + '}}',
            '|author = ' + author,
            '|date = ' + dato,
            '|permission = ',
            '|other_versions = ',
            '|other_fields = ',
            '}}',
            '',
            '=={{int:license-header}}==',
            license,
            '',
            ''].join('\n');
        $('#wpUploadDescription').val(desc);
        if (tittel != 'NOTFOUND') {
            $('#Bildetittel').html(tittel);
            imgFilename = tittel;
            if (year !== 0) {
                imgFilename += ' (' + year + ')';
            }
            imgFilename += '.jpg';
            $('#wpDestFile').parent().parent().removeClass('warning');
            $('#wpDestFile').next('.help-inline').hide();
        } else {
            $('#Bildetittel').html('-');
            imgFilename = getQueryVariable('filename', src);
            //$('#wpDestFile').parent().siblings('.warn').show();
            $('#wpDestFile').parent().parent().addClass('warning');
            $('#wpDestFile').next('.help-inline').show();
        }
        $('#wpDestFile').val(imgFilename);
    }

    $('#theform').on('submit', function(e) {
        var url = $('#inputurl').val();
        $.getJSON('./transfer_bg.fcgi', { 'url': url }, function(data) {
            if (data.hasOwnProperty('error')) {
                var emsg = "";
                if (data.error == 'duplicate') {
                    var url = 'http://commons.wikimedia.org/wiki/File:' + encodeURIComponent(data.filename);
                    emsg = "Bildet er <a href=\"" + url + "\">allerede overført til commons</a>";
                }
                $('#theform').append('<div class="alert alert-error">' + emsg + '</div>');
            } else {
                var imgLink = 'Lagre <strong><a href="' + data.src + '" target="_blank">filen</a></strong> lokalt på din maskin først (høyreklikk og Lagre som...), og trykk deretter: ',
                    d = new Date(),
                    current_year = d.getFullYear();
                $('#theform .alert').remove();

                src = data.src;
                license = data.license;
                author = data.metadata.Fotograf;
                dato = data.metadata.Datering;
                institusjon = data.metadata.Eierinstitusjon;
                inst = kortform(institusjon);
                bildenr = data.metadata.Bildenummer;
                samling = data.metadata['Arkiv/Samling'];
                historikk = data.metadata.Historikk;
                motiv = data.metadata.Motiv;
                tittel = data.metadata.Bildetittel;
                
                year = parseInt(data.year);
                if (dato == 'NOTFOUND') {
                    dato = '{{Unknown|date}}';
                    $('#Datering').html('<em>Ukjent</em>');
                } else {
                    $('#Datering').html(dato);
                }

                if (historikk != "NOTFOUND") {
                    $('#Historikk').html(historikk);
                } else {
                    $('#Historikk').html('-');
                }
                if (tittel != 'NOTFOUND') {
                    $('#Bildetittel').html(tittel);
                } else {
                    $('#Bildetittel').html('-');
                }
                if (author != 'NOTFOUND') {
                    $('#Fotograf').html(author);
                } else {
                    author = '{{Unknown|author}}';
                    //$('#Fotograf').html('<span class="warning">Uh oh, fant ikke bildets fotograf! Sjekk om fotografens navn kan være oppgitt i det grå feltet nederst på selve bildet.</span>');
                    $('#Fotograf').siblings('.warn').show();

                }
                if (motiv != "NOTFOUND") {
                    $('#Motiv').html(motiv);
                } else {
                    $('#Motiv').html('-');
                }
                
                var avbildet = Array();
                $.each(data.metadata['Avbildet sted'].split('|'), function(i, k) {
                    if (k != 'NOTFOUND') {
                        avbildet.push('<span class="key">' + $.trim(k) + '</span> (sted)');
                    }
                });
                $.each(data.metadata['Utsikt over'].split('|'), function(i, k) {
                    if (k != 'NOTFOUND') {
                        avbildet.push('<span class="key">' + $.trim(k) + '</span> (utsikt over)');
                    }
                });
                $.each(data.metadata['Utsikt over'].split('|'), function(i, k) {
                    if (k != 'NOTFOUND') {
                        avbildet.push('<span class="key">' + $.trim(k) + '</span> (utsikt over)');
                    }
                });
                var emneord = Array();
                if (data.metadata['Emneord'] != 'NOTFOUND') {
                    $.each(data.metadata['Emneord'].split('|'), function(i, k) {
                        emneord.push('<span class="key">' + $.trim(k) + '</span>');
                    });
                }
                $('#Avbildet').html(avbildet.join(' '));
                $('#Emneord').html(emneord.join(' '));
                $('#imgLink').html(imgLink);
                
                $('div#info').show();

                //if (current_year - year > 100) {
                //    license = 'pd-old-100';
                //}

                switch (license) {
                    case 'pd':
                        var lisens = 'Bildet er falt i det fri. (Valgene under er foreløpig ukomplette!)<ul>' +
                            '<li>Mal for Norge: <select class="license input-xxlarge">' +
                            '<option value="{{PD-Norway50}}">{{PD-Norway50}} Vanlig fotografi</option>' +
                            '<option value="{{PD-old-70}}">{{PD-old-70}} Åndsverk</option>' +
                            '<option value="{{PD-anon-70}}">{{PD-anon-70}} Åndsverk med ukjent fotograf</option>' +
                            '</select></li>';

                        lisens += '<li>Mal for USA: <select class="license input-xxlarge"><option value="">Velg:</option>';
                        var sel = '';
                        if (year < 1923) {
                            sel = 'selected="selected"'
                        }
                        lisens += '<option value="{{PD-1923}}"'+sel+'>{{PD-1923}} Bildet er publisert før 1923.</option>';
                        //license = '{{PD-Norway50}}\n{{PD-1923}}';
                        
                        lisens += '</select></li></ul><button id="license-btn">Ok</button>';
                        $('#Lisens').html('<div class="ok">' + lisens + '</div>');
                        $('#license-btn').click(function() {
                            $('form#upload').show();
                            fill_desc();
                        });
                        break;
                    case 'by-sa':
                        $('#Lisens').html('<div class="ok">CC-BY-SA er en <a href="//commons.wikimedia.org/wiki/Commons:Licensing">akseptabel lisens</a>.</div>');
                        license = 'cc-by-sa-3.0';
                        $('form#upload').show();
                        fill_desc();
                        break;
                    case 'by-nc-nd':
                        $('#Lisens').html('<div class="fail">CC-BY-NC-ND er ikke en <a href="//commons.wikimedia.org/wiki/Commons:Licensing">akseptabel lisens</a>.</div>');
                        return;
                    default:
                        $('#Lisens').html('<div class="fail">Klarte ikke å gjenkjenne lisensen.</div>');
                }

            }

        });
        return false;
    });

    $('form#upload :submit').on('click', function(e) {
        $('form#upload').attr('action', 'http://commons.wikimedia.org/w/index.php?title=Special:Upload&uploadformstyle=basic&wpDestFile=' + encodeURIComponent($("#wpDestFile").val()));
    });

});
