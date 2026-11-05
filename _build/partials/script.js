(function(){
  var d=document;
  d.documentElement.classList.add('js');
  var reduce=window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  d.querySelectorAll('[data-year]').forEach(function(el){el.textContent=new Date().getFullYear();});

  var header=d.querySelector('.header'), wa=d.querySelector('.wa-float'), ticking=false;
  function onScroll(){var y=window.scrollY;header.classList.toggle('is-scrolled',y>8);wa.classList.toggle('is-visible',y>window.innerHeight*.8);ticking=false;}
  window.addEventListener('scroll',function(){if(!ticking){requestAnimationFrame(onScroll);ticking=true;}},{passive:true});
  onScroll();

  var burger=d.querySelector('.burger'), mnav=d.getElementById('mnav');
  function setMenu(open){
    burger.setAttribute('aria-expanded',String(open));
    burger.setAttribute('aria-label',open?'Cerrar menú':'Abrir menú');
    mnav.classList.toggle('is-open',open);
    d.body.style.overflow=open?'hidden':'';
  }
  burger.addEventListener('click',function(){setMenu(burger.getAttribute('aria-expanded')!=='true');});
  mnav.addEventListener('click',function(e){if(e.target.closest('a'))setMenu(false);});
  d.addEventListener('keydown',function(e){if(e.key==='Escape'&&mnav.classList.contains('is-open')){setMenu(false);burger.focus();}});
  window.matchMedia('(min-width:1060px)').addEventListener('change',function(m){if(m.matches)setMenu(false);});

  var hero=d.querySelector('.hero');
  if(hero)requestAnimationFrame(function(){requestAnimationFrame(function(){hero.classList.add('is-ready');});});

  var items=d.querySelectorAll('[data-reveal]');
  if('IntersectionObserver' in window && !reduce){
    var io=new IntersectionObserver(function(entries){
      entries.forEach(function(en){if(en.isIntersecting){en.target.classList.add('is-in');io.unobserve(en.target);}});
    },{rootMargin:'0px 0px -6% 0px',threshold:.1});
    items.forEach(function(el){io.observe(el);});
  }else{items.forEach(function(el){el.classList.add('is-in');});}


  var form=d.getElementById('lead-form');
  if(form)(function(){
  var started=Date.now(), status=d.getElementById('form-status'), btn=form.querySelector('button[type="submit"]');
  var emailRe=/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;
  function validateField(el){
    var ok=el.checkValidity()&&!!el.value.trim();
    if(el.type==='email'&&ok)ok=emailRe.test(el.value.trim());
    el.closest('.field').classList.toggle('has-error',!ok);
    el.setAttribute('aria-invalid',String(!ok));
    return ok;
  }
  form.querySelectorAll('.input').forEach(function(el){
    el.addEventListener('blur',function(){if(el.value)validateField(el);});
    el.addEventListener('input',function(){if(el.closest('.field').classList.contains('has-error'))validateField(el);});
    el.addEventListener('change',function(){if(el.tagName==='SELECT')validateField(el);});
  });
  function showSuccess(){
    d.getElementById('form-wrap').hidden=true;
    var s=d.getElementById('form-success');
    s.classList.add('is-visible');
    s.focus({preventScroll:true});
    s.scrollIntoView({behavior:reduce?'auto':'smooth',block:'center'});
  }
  function setStatus(msg,err){status.textContent=msg;status.classList.toggle('is-error',!!err);}
  form.addEventListener('submit',function(e){
    e.preventDefault();setStatus('');
    var firstBad=null;
    form.querySelectorAll('.input').forEach(function(el){if(!validateField(el)&&!firstBad)firstBad=el;});
    if(firstBad){firstBad.focus();setStatus('Revisa los campos marcados.',true);return;}
    if(form.website.value||Date.now()-started<2500){showSuccess();return;}
    var endpoint=form.getAttribute('data-endpoint');
    if(!endpoint){
      var body='Nombre: '+form.nombre.value+'\nEmpresa: '+form.empresa.value+'\nCorreo: '+form.email.value+'\nEspecialidad: '+form.especialidad.value+'\n\n'+form.mensaje.value;
      window.location.href='mailto:'+form.getAttribute('data-mailto')+'?subject='+encodeURIComponent('Solicitud de evaluación — '+form.especialidad.value)+'&body='+encodeURIComponent(body);
      setStatus('Abrimos tu aplicación de correo con la solicitud lista para enviar.');
      return;
    }
    var data=new FormData(form);data.delete('website');
    data.append('_subject','Nueva solicitud de evaluación — '+form.especialidad.value);
    btn.setAttribute('aria-busy','true');
    fetch(endpoint,{method:'POST',body:data,headers:{'Accept':'application/json'}})
      .then(function(r){if(!r.ok)throw new Error(r.status);showSuccess();})
      .catch(function(){setStatus('No pudimos enviar tu solicitud. Inténtalo nuevamente o escríbenos a contacto@cykingenieros.cl.',true);})
      .then(function(){btn.removeAttribute('aria-busy');});
  });
  })();
})();
