import React from "react";
import { useLocation } from "react-router-dom";
import { Link } from "react-router-dom";
import Header from "../components/Header";
import Footer from "../components/Footer";

const NotFound = () => {
  const location = useLocation();

  return (
    <div className="min-h-screen flex flex-col bg-cream">
      <Header />

      <main className="flex-grow container mx-auto px-4 py-8 flex items-center justify-center">
        <div className="bg-white dark:bg-card rounded-lg shadow-lg p-8 border border-light-blue dark:border-gray-700 max-w-lg w-full text-center">
          <h1 className="text-6xl font-bold mb-4 font-sreda text-navy-blue">
            404
          </h1>
          <p className="text-xl text-gray-700 mb-6 font-josefin">
            Oops! The page you're looking for cannot be found.
          </p>
          <p className="text-gray-600 mb-8">
            The path{" "}
            <span className="font-mono bg-light-blue px-2 py-1 rounded">
              {location.pathname}
            </span>{" "}
            does not exist on our website.
          </p>
          <Link
            to="/"
            className="px-6 py-3 bg-navy-blue text-white rounded-md hover:bg-medium-blue transition-colors font-josefin inline-block"
          >
            Back to Home
          </Link>
        </div>
      </main>
      <Footer />
    </div>
  );
};

export default NotFound;
