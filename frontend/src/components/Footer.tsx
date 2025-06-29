import React from "react";

const Footer = () => {
  return (
    <footer className="bg-brand-primary dark:bg-gray-950 text-white py-8 transition-colors duration-300">
      <div className="container mx-auto px-4">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          <div>
            <h3 className="text-lg font-bold mb-4">About Us</h3>
            <p className="text-sm">
              Diidemo.hr - Your ultimate platform for discovering amazing events
              near you across Croatia.
            </p>
          </div>
          <div>
            <h3 className="text-lg font-bold mb-4">Quick Links</h3>
            <ul className="text-sm">
              <li className="mb-2">
                <a href="#" className="hover:text-medium-blue">
                  Home
                </a>
              </li>
              <li className="mb-2">
                <a href="#" className="hover:text-medium-blue">
                  Events
                </a>
              </li>
              <li className="mb-2">
                <a href="#" className="hover:text-medium-blue">
                  Venues
                </a>
              </li>
              <li className="mb-2">
                <a href="#" className="hover:text-medium-blue">
                  About
                </a>
              </li>
              <li className="mb-2">
                <a href="#" className="hover:text-medium-blue">
                  Contact
                </a>
              </li>
            </ul>
          </div>
          <div>
            <h3 className="text-lg font-bold mb-4">Contact Us</h3>
            <p className="text-sm mb-2">Email: info@diidemo.hr</p>
            <p className="text-sm mb-2">Phone: +385 1 234 5678</p>
            <p className="text-sm">Address: Zagreb, Croatia</p>
          </div>
        </div>
        <div className="mt-8 text-center text-sm">
          <p>&copy; 2024 Diidemo.hr. All rights reserved.</p>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
