import React from 'react';
import { Logo } from './Logo';

/**
 * LogoShowcase component for demonstrating and testing all logo variants
 * This is useful for development and design system documentation
 */
export const LogoShowcase: React.FC = () => {
  return (
    <div className="p-8 bg-gray-50 min-h-screen">
      <div className="max-w-6xl mx-auto space-y-12">
        <div className="text-center">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            Diidemo.hr Logo System
          </h1>
          <p className="text-xl text-gray-600 max-w-2xl mx-auto">
            Responsive, accessible, and design-system integrated logo components
            with multiple variants for different use cases.
          </p>
        </div>

        {/* Variants Section */}
        <section className="space-y-8">
          <h2 className="text-2xl font-semibold text-gray-900">Logo Variants</h2>
          
          <div className="grid gap-8 md:grid-cols-3">
            <div className="bg-white p-6 rounded-lg shadow-sm border">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Full Logo</h3>
              <div className="flex items-center justify-center h-32 bg-gray-50 rounded-lg mb-4">
                <Logo variant="full" />
              </div>
              <p className="text-sm text-gray-600">
                Complete logo with tagline. Best for headers, footers, and marketing materials.
              </p>
            </div>

            <div className="bg-white p-6 rounded-lg shadow-sm border">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Compact Logo</h3>
              <div className="flex items-center justify-center h-32 bg-gray-50 rounded-lg mb-4">
                <Logo variant="compact" />
              </div>
              <p className="text-sm text-gray-600">
                Logo without tagline. Perfect for navigation bars and constrained spaces.
              </p>
            </div>

            <div className="bg-white p-6 rounded-lg shadow-sm border">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Icon Logo</h3>
              <div className="flex items-center justify-center h-32 bg-gray-50 rounded-lg mb-4">
                <Logo variant="icon" />
              </div>
              <p className="text-sm text-gray-600">
                Circular icon version. Ideal for favicons, app icons, and small spaces.
              </p>
            </div>
          </div>
        </section>

        {/* Sizes Section */}
        <section className="space-y-8">
          <h2 className="text-2xl font-semibold text-gray-900">Size Options</h2>
          
          <div className="bg-white p-6 rounded-lg shadow-sm border">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Fixed Sizes</h3>
            <div className="grid gap-4 md:grid-cols-6">
              <div className="text-center">
                <div className="flex items-center justify-center h-20 bg-gray-50 rounded-lg mb-2">
                  <Logo variant="compact" size="xs" />
                </div>
                <span className="text-sm text-gray-600">XS (24px)</span>
              </div>
              <div className="text-center">
                <div className="flex items-center justify-center h-20 bg-gray-50 rounded-lg mb-2">
                  <Logo variant="compact" size="sm" />
                </div>
                <span className="text-sm text-gray-600">SM (32px)</span>
              </div>
              <div className="text-center">
                <div className="flex items-center justify-center h-20 bg-gray-50 rounded-lg mb-2">
                  <Logo variant="compact" size="md" />
                </div>
                <span className="text-sm text-gray-600">MD (48px)</span>
              </div>
              <div className="text-center">
                <div className="flex items-center justify-center h-20 bg-gray-50 rounded-lg mb-2">
                  <Logo variant="compact" size="lg" />
                </div>
                <span className="text-sm text-gray-600">LG (64px)</span>
              </div>
              <div className="text-center">
                <div className="flex items-center justify-center h-20 bg-gray-50 rounded-lg mb-2">
                  <Logo variant="compact" size="xl" />
                </div>
                <span className="text-sm text-gray-600">XL (80px)</span>
              </div>
              <div className="text-center">
                <div className="flex items-center justify-center h-20 bg-gray-50 rounded-lg mb-2">
                  <Logo variant="compact" size="fluid" />
                </div>
                <span className="text-sm text-gray-600">Fluid</span>
              </div>
            </div>
          </div>
        </section>

        {/* Responsive Behavior Section */}
        <section className="space-y-8">
          <h2 className="text-2xl font-semibold text-gray-900">Responsive Behavior</h2>
          
          <div className="bg-white p-6 rounded-lg shadow-sm border">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Fluid Sizing</h3>
            <p className="text-sm text-gray-600 mb-4">
              Resize your browser window to see the logo scale responsively
            </p>
            <div className="space-y-6">
              <div className="bg-gray-50 p-4 rounded-lg">
                <div className="text-sm text-gray-600 mb-2">Full Logo (200px - 400px)</div>
                <Logo variant="full" size="fluid" />
              </div>
              <div className="bg-gray-50 p-4 rounded-lg">
                <div className="text-sm text-gray-600 mb-2">Compact Logo (120px - 240px)</div>
                <Logo variant="compact" size="fluid" />
              </div>
              <div className="bg-gray-50 p-4 rounded-lg">
                <div className="text-sm text-gray-600 mb-2">Icon Logo (32px - 48px)</div>
                <Logo variant="icon" size="fluid" />
              </div>
            </div>
          </div>
        </section>

        {/* Dark Theme Section */}
        <section className="space-y-8">
          <h2 className="text-2xl font-semibold text-gray-900">Dark Theme Support</h2>
          
          <div className="bg-secondary-900 text-white p-6 rounded-lg">
            <h3 className="text-lg font-medium mb-4">Dark Background</h3>
            <div className="grid gap-6 md:grid-cols-3">
              <div className="text-center">
                <Logo variant="full" className="text-white" />
                <p className="text-sm text-gray-300 mt-2">Full on Dark</p>
              </div>
              <div className="text-center">
                <Logo variant="compact" className="text-white" />
                <p className="text-sm text-gray-300 mt-2">Compact on Dark</p>
              </div>
              <div className="text-center">
                <Logo variant="icon" className="text-white" />
                <p className="text-sm text-gray-300 mt-2">Icon on Dark</p>
              </div>
            </div>
          </div>
        </section>

        {/* Accessibility Section */}
        <section className="space-y-8">
          <h2 className="text-2xl font-semibold text-gray-900">Accessibility Features</h2>
          
          <div className="bg-white p-6 rounded-lg shadow-sm border">
            <div className="grid gap-4 md:grid-cols-2">
              <div>
                <h3 className="text-lg font-medium text-gray-900 mb-2">Screen Reader Support</h3>
                <ul className="text-sm text-gray-600 space-y-1">
                  <li>• ARIA labels and roles</li>
                  <li>• SVG title and description elements</li>
                  <li>• Semantic HTML structure</li>
                  <li>• Keyboard navigation support</li>
                </ul>
              </div>
              <div>
                <h3 className="text-lg font-medium text-gray-900 mb-2">Visual Accessibility</h3>
                <ul className="text-sm text-gray-600 space-y-1">
                  <li>• High contrast mode compatible</li>
                  <li>• Scalable vector graphics</li>
                  <li>• Proper color contrast ratios</li>
                  <li>• Reduced motion support</li>
                </ul>
              </div>
            </div>
          </div>
        </section>

        {/* Usage Examples Section */}
        <section className="space-y-8">
          <h2 className="text-2xl font-semibold text-gray-900">Usage Examples</h2>
          
          <div className="bg-white p-6 rounded-lg shadow-sm border">
            <div className="space-y-6">
              <div>
                <h3 className="text-lg font-medium text-gray-900 mb-2">Navigation Header</h3>
                <div className="bg-gray-50 p-4 rounded-lg">
                  <div className="flex items-center justify-between">
                    <Logo variant="compact" size="fluid" maxWidth="180px" minWidth="120px" />
                    <div className="flex space-x-4">
                      <span className="text-sm text-gray-600">Menu Item</span>
                      <span className="text-sm text-gray-600">Menu Item</span>
                    </div>
                  </div>
                </div>
                <pre className="text-xs text-gray-600 mt-2 bg-gray-50 p-2 rounded">
{`<Logo 
  variant="compact" 
  size="fluid" 
  maxWidth="180px" 
  minWidth="120px" 
/>`}
                </pre>
              </div>

              <div>
                <h3 className="text-lg font-medium text-gray-900 mb-2">Footer</h3>
                <div className="bg-secondary-900 text-white p-4 rounded-lg">
                  <Logo variant="full" size="fluid" maxWidth="320px" minWidth="240px" className="text-white" />
                </div>
                <pre className="text-xs text-gray-600 mt-2 bg-gray-50 p-2 rounded">
{`<Logo 
  variant="full" 
  size="fluid" 
  maxWidth="320px" 
  minWidth="240px" 
  className="text-white" 
/>`}
                </pre>
              </div>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
};