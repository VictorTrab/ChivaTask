# Contexto de Dominio

## ChivaTask

Nombre de producto de la app. Comunica una herramienta util, juvenil y enfocada en tareas academicas.

## Campus UPH

Portal Moodle de la Universidad Politecnica de Honduras usado por estudiantes para revisar cursos, tareas y entregas.

## Moodle API

Servicios web oficiales de Moodle usados por la app. En v1 reemplazan cualquier scraping.

## Curso Visible

Curso activo y visible para el estudiante segun Moodle. La app ignora cursos ocultos.

## Tarea

Asignacion Moodle que puede tener nombre, curso, fecha de entrega, URL y estado de entrega.

## Entrega

Registro de Moodle que indica si el estudiante ya envio una tarea.

## Pendiente

Tarea cuyo estado de entrega indica que no hay entrega registrada. En v1 los estados pendientes son `new`, `reopened` y `draft`.

## Tarea Vencida

Pendiente con fecha de entrega anterior al momento actual.

## Tarea Sin Fecha

Pendiente que Moodle publica sin fecha de entrega. Se muestra separada y no se trata como "vence pronto".

## Snooze

Posposicion local de recordatorio. No cambia el estado de Moodle.

## Cache Local

Datos minimos en SQLite para mostrar pendientes y evitar repetir notificaciones. No contiene contrasenas ni tokens.

## Sincronizacion

Proceso de consultar Moodle API, actualizar cache local, detectar cambios y devolver un resultado estable a la UI.
