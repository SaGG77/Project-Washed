// static/js/delete.js

document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll("form.js-delete-form").forEach((form) => {
        form.addEventListener("submit", async  (e) => {
            e.preventDefault();

            const r = await Swal.fire({
                title: "¿Eliminar?",
                text: "Esta acción no se puede deshacer",
                icon: "warning",
                showCancelButton: true,
                confirmButtonText: "Si, eliminar",
                cancelButtonText: "Cancelar",
            });
            if (r.isConfirmed) form.submit(); // se recarga con flask que tambien borra
        });
    });
});