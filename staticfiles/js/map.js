/**
 * Gestion de la carte pour afficher les livreurs disponibles
 * Utilise Leaflet.js pour l'affichage de la carte
 */
document.addEventListener('DOMContentLoaded', function () {
    // Initialiser la carte centrée sur Conakry, Guinée
    const map = L.map('deliveryMap').setView([9.6412, -13.5784], 12);

    // Ajouter la couche OpenStreetMap
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }).addTo(map);

    // Récupérer les données des livreurs depuis l'élément HTML
    const deliveryPersonsData = JSON.parse(document.getElementById('delivery-persons-data').textContent);

    // Ajouter des marqueurs pour chaque livreur
    deliveryPersonsData.forEach(person => {
        if (person.latitude && person.longitude) {
            const marker = L.marker([person.latitude, person.longitude]).addTo(map);
            marker.bindPopup(`
                <strong>${person.username}</strong><br>
                Téléphone: ${person.phone_number}<br>
                Statut: ${person.availability_status}<br>
                <button onclick="selectDeliveryPerson(${person.user_id}, '${person.username}')">Sélectionner ce livreur</button>
            `);
        }
    });

    // Fonction pour sélectionner un livreur
    window.selectDeliveryPerson = function (userId, username) {
        const proposedCost = prompt(`Entrez le prix proposé pour ${username} (en €) :`);
        if (proposedCost && !isNaN(proposedCost) && proposedCost > 0) {
            document.getElementById('delivery_person_id').value = userId;
            document.getElementById('proposed_cost').value = proposedCost;
            document.getElementById('assign-delivery-form').submit();
        } else {
            alert('Veuillez entrer un prix valide.');
        }
    };
});