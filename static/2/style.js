var vars = {};

var update = function update() {
    // Updating Footer and Nav
    vars.footer = document.getElementsByTagName('footer')[0];
    vars.nav = document.getElementsByTagName('nav')[0];
    vars.footerRect = vars.footer.getBoundingClientRect();
    vars.navRect = vars.nav.getBoundingClientRect();
    vars.section = document.getElementsByTagName('section')[0]
    vars.sectionRect = vars.section.getBoundingClientRect();
    // FOOTER CHANGING
    if (Number(window.innerWidth) > 640) {
        if (vars.sectionRect.bottom + vars.footerRect.height < Number(window.innerHeight)) {
            vars.footer.style = 'position: fixed; bottom: 0;';
        } else {
            vars.footer.style = 'position: static;';
        }
    } else {
        vars.footer.style = 'position: static;';
    }
    // NAV CHANGING
    if (vars.sectionRect.top < 40) {
        vars.nav.style = 'box-shadow: grey 0px 5px 15px; border-top: 0; position: fixed; top: 0';
        vars.section.style = 'margin-top: 40px;';
    } else if (vars.sectionRect.top >= 40 && vars.sectionRect.top <= 42) {
        vars.nav.style = 'box-shadow: 0; border-top: 0; position: fixed;';
    } else {
        if (vars.navRect.top <= 0) {
            vars.nav.style = 'box-shadow: 0; border-top: 2px solid #0AF; position: static;';
        } else {
            vars.nav.style = 'box-shadow: 0; position: static;';
        }
        vars.section.style = 'margin-top: 0;';
    }
    window.requestAnimationFrame(update);
}

update();
