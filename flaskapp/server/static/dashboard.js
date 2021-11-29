
function totalResult(t_ks, t_es, t_mm, p_ks, p_es, p_mm) {
    var trace1 = {
    x: ['Kingstone', 'Eslite', 'Momo'],
    y: [t_ks, t_es, t_mm],
    name: 'Total Scraped',
    type: 'bar',
    opacity: 0.7,
    };

    var trace2 = {
    x: ['Kingstone', 'Eslite', 'Momo'],
    y: [p_ks, p_es, p_mm],
    name: 'Price Updated',
    type: 'bar',
    opacity: 0.7,
    marker: {
        color: 'rgb(158,202,225)',
    } 
    };

    var data = [trace1, trace2];

    var layout = {
        title: 'Web Scrap Result',
        barmode: 'group'
    };
    Plotly.newPlot('totalResult', data, layout);
}

function gapCheck(ks_dup, ks_unmatch, ks_new, ks_out, es_dup, es_unmatch, es_new, es_out, mm_dup, mm_unmatch, mm_new, mm_out) {
    var trace1 = {
    x: ['Kingstone', 'Eslite', 'Momo'],
    y: [ks_dup, es_dup, mm_dup],
    name: 'Duplicate Found',
    type: 'bar',
    opacity: 0.7,
    };

    var trace2 = {
    x: ['Kingstone', 'Eslite', 'Momo'],
    y: [ks_unmatch, es_unmatch, mm_unmatch],
    name: 'Unmatched Books',
    type: 'bar',
    opacity: 0.7,
    marker: {
        color: 'rgb(138,160,180)',
    } 
    };
    var trace3 = {
    x: ['Kingstone', 'Eslite', 'Momo'],
    y: [ks_new, es_new, mm_new],
    name: 'New Books',
    type: 'bar',
    opacity: 0.7,
    marker: {
        color: 'rgb(158,180,200)',
    } 
    };
    var trace4 = {
    x: ['Kingstone', 'Eslite', 'Momo'],
    y: [ks_out, es_out, mm_out],
    name: 'Phase Out',
    type: 'bar',
    opacity: 0.7,
    marker: {
        color: 'rgb(158,202,225)',
    } 
    };    
    var data = [trace1, trace2, trace3, trace4];

    var layout = {
        title: 'Book catalog Gap Check',
        barmode: 'group'
    };
    Plotly.newPlot('gapCheck', data, layout);
}


function newRegistration(ks_isbn, es_isbn, mm_isbn) {
    var data = [
        {
          x: ['Kingstone', 'Eslite', 'Momo'],
          y: [ks_isbn, es_isbn, mm_isbn],
          type: 'bar',
          marker: {
            color: 'rgb(158,202,225)',
        } 
        }
      ];
      
    var layout = {
        title: 'New Books Registered',
    };
    Plotly.newPlot('newRegistration', data, layout);
}




function timeSpent(
    ks_first, ks_remove, ks_check_unmatch, ks_phase_out, ks_update_price, ks_ttl,
    es_first, es_remove, es_check_unmatch, es_phase_out, es_update_price, es_ttl,
    mm_first, mm_remove, mm_check_unmatch, mm_phase_out, mm_update_price, mm_ttl
){
    var values = [
        ['First Scrap', 'Remove Duplicate Found', 'Check Unmatch Books', 'Scrap Phaseout', 'Update Price ', '<b>TOTAL</b>'],
        [ks_first, ks_remove, ks_check_unmatch, ks_phase_out, ks_update_price, ks_ttl],
        [es_first, es_remove, es_check_unmatch, es_phase_out, es_update_price, es_ttl],
        [mm_first, mm_remove, mm_check_unmatch, mm_phase_out, mm_update_price, mm_ttl]]
  
  var data = [{
    type: 'table',
    header: {
      values: [["<b>Time Spent</b>"], ["<b>Kingstone</b>"],
                   ["<b>Eslite</b>"], ["<b>Momo</b>"]],
      align: "center",
      fill: {color: "rgb(158,202,225)"},
      font: {family: "Arial", size: 12, color: "black"}
    },
    cells: {
      values: values,
      align: "center",
      font: {family: "Arial", size: 11, color: ["black"]}
    }
  }]
  var layout = {
    title: "Scrap Time In Detail"
  }
  Plotly.newPlot('timeSpent', data, layout);
}