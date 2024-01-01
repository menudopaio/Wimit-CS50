# FIXED:

(26/12/23)
1. Si filtro, da error y no muestra la pagina.
2. No aparecen los wimits privados de amigos.
3. Ordenar actividades por privado- hora, dia, publico- hora, dia.
4. En friends.html, no mostrar id del user friend.
5. Configurar redireccion error.html, va siempre a addwimit (no a search-friends, log in..).

(27/12/23)
6. Cuando le doy a add friend, redirige sin imagen.
7. Eliminar Guest. Asegurar que sin loguear no se puede crear actividades o añadir amigos.
8. Si hay algun friends_request status pending, que aparezca algun icono o algo en Friends en la cabecera.
9. En friends.html que se vea claro los amigos aceptados, rechazados o pendientes (verde, rojo, amarillo).
10. Eliminar tabla izquierda check_details.html.
11. En el grafico resumen del wimit hacer visible el status (FULL, Ready!, Need more people!)
12. Cuando hay participantes minimos sumando distintos horarios, no debe ser valido.
13. Nombre usuario en el nav bar

(28/12/23)
14. Si se edita un wimit, verificar que se actualiza la base de datos.
15. Arreglar testigo de Friends pending.
16. Globalizar funcion today y añadir datos de session['user_username'], session['friends_pending'].
17. Arreglado: en /add_wimit se puede poner un min mas alto que un max.
18. app.py y friends.html unificar sql queries.

(29/12/23)
19. Desde Home, 'All' del desplegable no funciona.

20. En home o mywimits, que aparezca el nombre real de la actividad en vez de "Others".
21. El grafico-pastel no aparece correctamente.
22. Revisar grafico check_details.html cuando solo hay una hora o dos. Muestra etiquetas de mas.
23. Asegurar que sin loguear no se puede crear actividades o añadir amigos etc.
24. Revisar seguridad basica de inputs.

(1/1/24)
25. Desplegable home lleva a home-filters con titulo de mywimits.
26. No se guardan correctamente los id de FRIENDS
27. Verificar si actividades privadas funcionan bien y se displeyean bien en home.
28. Arreglar all del desplegable MyWimits.
29. En home.html, if enrolled == True, que aparezca un testigo.