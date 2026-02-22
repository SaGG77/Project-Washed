// static/js/delete.js

document.addEventListener("DOMContentLoaded", () => {
    const forms = document.querySelectorAll("form.js-delete-form");

    forms.forEach((form) => {
        form.addEventListener("submit", async (e) => {
            e.preventDefault();

            const ok = confirm("¿Seguro que quieres eliminar esto?")
            if (!ok) return;

            try {
                const response = await fetch(form.action, {
                    method: "POST",
                    body: new FormData(form),
                    headers: {
                        "X-Requested-With": "XMLHttpRequest"
                    },
                });

                // Si hay error se manda esta vaina
                if (!response.ok) {
                    alert("No se pudo eliminar. Intenta otra vez.");
                    return;
                }

                const card = form.closest("[data-item-id]");
                if (card) {
                    card.remove();
                } else {
                    window.location.reload();
                }
                // Si el proceso se cae en algun momento(sin internet, servidor caido), desde el try, pues cae aquí
            } catch (err) {
                console.error(err);
                alert("Error de red. Revisa tu conexion")
            } 
        });
    });
});
