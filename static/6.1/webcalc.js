var pgadd = document.getElementById('pg-add');
var dbadd = document.getElementById('db-add');

var db = {
    pages: 0,
    databases: 0,
    pg: [document.getElementById('page-0')],
    db: [document.getElementById('db-0')]
}

var newPage = function() {
    let pgtr = document.createElement('tr')
    let pgdel = document.createElement('td')
    let pgtype = document.createElement('td')
    let pgtitle = document.createElement('td')
    let pgsm = document.createElement('td')
    
    db.pages++
    
    pgtr.setAttribute('id', "page-"+db.pages)
    
    pgdel.innerHTML = '<button class="del-btn" onclick="deletePage('+db.pages+')">X</button>'
    pgtype.innerHTML = "<select><option selected disabled>Choose</option><option>Basic</option><option>Forum</option><option>Blog</option><option>Login</option></select>"
    pgtitle.innerHTML = "<input type='text'>"
    pgsm.innerHTML = "<input type='checkbox' id='page-sm-"+db.pages+"'>"
    
    pgtr.appendChild(pgdel)
    pgtr.appendChild(pgtype)
    pgtr.appendChild(pgtitle)
    pgtr.appendChild(pgsm)
    
    db.pg.push(pgtr);
    
    pgadd.parentNode.insertBefore(pgtr, pgadd)
}

var newDB = function() {
    let dbtr = document.createElement('tr')
    let dbdel = document.createElement('td')
    let dbtype = document.createElement('td')
    
    db.databases++
    
    dbtr.setAttribute('id', "db-"+db.databases)
    dbtype.setAttribute('colspan', 2)
    
    dbdel.innerHTML = '<button class="del-btn" onclick="deleteDB('+db.databases+')">X</button>'
    dbtype.innerHTML = "<select><option selected disabled>Choose</option><option>User</option><option>Blog</option><option>Forum</option><option>Other</option></select>"
    
    dbtr.appendChild(dbdel)
    dbtr.appendChild(dbtype)
    
    db.db.push(dbtr)
    
    dbadd.parentNode.insertBefore(dbtr, dbadd)
}

var deletePage = function(id) {
    for ( i = 0; i < db.pg.length; i++ ) {
        if (db.pg[i].id == ('page-' + id)) {
            db.pg[i].remove()
            db.pg.splice(i, 1);
        }
    }
}

var deleteDB = function(id) {
    for ( i = 0; i < db.db.length; i++ ) {
        if (db.db[i].id == ('db-' + id)) {
            db.db[i].remove()
            db.db.splice(i, 1);
        }
    }
}

var calc = function() {
    let dbon = document.getElementById('db-on')
    let price = 0.00;
    if (dbon.checked == true) {
        price += (db.db.length * 5.00);
    }
    price += (db.pg.length * 20.00);
    for ( i = 0; i < db.pg.length; i++ ) {
        let num = db.pg[i].cells.length -1
        let sm = db.pg[i].cells[num].children[0]
        //console.log(i, sm)
        if ( sm.checked == true ) {
            price += 10.00;
        }
    }
    for ( d = 0; d < db.db.length; d++ ) {
        let cdb = db.db[d];
        if ( cdb.cells[1].children[0].value == 'Other' && !cdb.cells[2] ) {
            cdb.insertCell();
            cdb.cells[1].setAttribute('colspan', 1);
            cdb.cells[2].setAttribute('colspan', 1);
            cdb.cells[2].innerHTML = "<input type='text' placeholder='Name'>";
        } else if ( cdb.cells[1].children[0].value != 'Other' && cdb.cells[2] ) {
            cdb.deleteCell(2);
            cdb.cells[1].setAttribute('colspan', 2);
        }
    }
    for ( d = 0; d < db.pg.length; d++ ) {
        let cpg = db.pg[d];
        if (cpg.cells[1].children[0].value != 'Basic' && cpg.cells.length == 4){
            console.log('Shrinking table row')
            cpg.deleteCell(2);
            cpg.cells[1].setAttribute('colspan', 2);
        } else if (cpg.cells[1].children[0].value == 'Basic' && cpg.cells.length == 3) {
            console.log('Expand table row')
            cpg.deleteCell(2);
            cpg.insertCell();
            cpg.insertCell();
            cpg.cells[2].innerHTML = "<input type='text'>";
            cpg.cells[3].innerHTML = "<input type='checkbox' id='page-sm-"+d+"'>";
            cpg.cells[1].setAttribute('colspan', 1);
        }
        let type = cpg.cells[1].children[0]
        let cellnum = cpg.cells.length-1
        switch ( type.value ) {
            case 'Forum':
                cpg.cells[cellnum].children[0].checked = true;
                break;
            case 'Blog':
                cpg.cells[cellnum].children[0].checked = true;
                break;
            case 'Login':
                cpg.cells[cellnum].children[0].checked = false;
                break;
        }
    }
    
    document.getElementById('output').innerText = '$'+price+'.00';
    window.requestAnimationFrame(calc)
}

calc()
